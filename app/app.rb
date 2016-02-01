require 'rubygems'
require 'sinatra'
require 'haml'
require 'json'
require 'sinatra/flash'
require 'sinatra/partial'
require 'i18n'
require 'i18n/backend/fallbacks'
require './resq_db'

configure do
  #set :environment, :production
  set :show_exceptions, false #if production?
  enable :sessions
  set :session_secret, '*&(^B234q56g!'
  enable :logging

  # I18n settings
  I18n::Backend::Simple.send(:include, I18n::Backend::Fallbacks)
  I18n.load_path = Dir[File.join(settings.root, 'locales', '*.yml')]
  I18n.default_locale = :de
  I18n.config.available_locales = [I18n.default_locale, :en]
  I18n.backend.load_translations
#  set :show_exceptions, :after_handler #if development?
end

configure :development do
  require "sinatra/reloader"
  set :raise_errors, true
end

helpers do
  def username
    session[:identity] ? session[:identity] : I18n.t('messages.hello_stranger')
  end

  def logged_in?
    session[:identity]
  end

  def i18n_link(url)
    "/#{I18n.locale}#{url}"
  end

  def switch_lang(lang)
    "/#{lang.to_s}#{request.path}"
  end

  def db_exist?
    File.exist?("/home/pi/.resq-pi/resq-pi.db")
  end
end

before '/:locale/*' do
  I18n.locale = params[:locale]
  request.path_info = '/' + params[:splat][0]
end

before '/admin/*' do
  unless session[:identity]
    session[:previous_url] = request.path
    flash[:error] = 'Sorry, you need to be logged in to visit ' + request.path
    halt haml(:login_form)
  end
end

get '/' do
  halt "Sorry, no database yet ... please execute 'sudo ~/alarm_pi.py --resetdb --verbose'" unless db_exist?
  @sms_list = Participant.sms_list
  @email_list = Participant.email_list
  @setting = Setting.first
  @alarm_logs = ResqLog.all.order(created_at: :desc)
  haml :info
end

get '/login/form' do
  haml :login_form
end

post '/login/attempt' do
  setting = Setting.new
  if setting.password_ok?(params[:password])
    session[:identity] = setting.identity
    flash[:notice] = I18n.t('notices.logged_in')
    redirect to i18n_link('/admin/settings')
  else
    flash[:error] = I18n.t('errors.wrong_password')
    redirect to i18n_link('/login/form')
  end
end

get '/admin/password' do
  haml :password
end

post '/admin/change_password' do
  setting = Setting.new
  if params[:new_password].length < 6
    flash[:error] = I18n.t('errors.password_too_short')
  elsif params[:new_password] != params[:again_password]
    flash[:error] = I18n.t('errors.password_confirmation')
  elsif setting.change_password(params[:current_password], params[:new_password])
    flash[:notice] = I18n.t('notices.password_changed')
  else
    flash[:error] = I18n.t('error.generic_error')
  end
  redirect to i18n_link('/admin/password')
end

get '/admin/settings' do
  @setting = Setting.first
  haml :settings
end

post '/admin/change_settings' do
  errors = []
  if params[:username].blank?
    errors << I18n.t('errors.your_name_required')
  end

  params[:use_sms] = 0 if params[:use_sms].blank?
  params[:use_email] = 0 if params[:use_email].blank?

  if params[:use_sms] == '1' or params[:use_email] == '1'
    # check params for sms notifications
    if params[:use_sms] == '1'
      if params[:phone_number].blank?
        errors << I18n.t('errors.your_phone_number_required')
      end
    end

    # check params for email notification
    if params[:use_email] == '1'
      if params[:email_address].blank?
        errors << I18n.t('errors.email_address_required')
      end
      if params[:email_password].blank?
        errors << I18n.t('errors.email_password_required')
      end
      if params[:email_login].blank?
        errors << I18n.t('errors.username_required')
      end
      if params[:smtp].blank?
        errors << I18n.t('errors.smtp_server_required')
      end
      if params[:port].blank?
        errors << I18n.t('errors.smtp_port_required')
      end
    end
  else
    errors << I18n.t('errors.sms_or_email_notification')
  end

  if errors.empty?
    settings = Setting.first
    settings.update_attributes(params)
    flash.now[:notice] = I18n.t('notices.changes_saved')
    redirect to i18n_link('/admin/settings')
  else
    flash.now[:error] = errors.join("<br>")
    @setting = Setting.first
    @setting.attributes = params
    haml :settings
  end
end

get '/admin/participants' do
  haml :participants
end

delete "/admin/participants/:id/delete" do
  Participant.destroy(params[:id])
  haml :participants
end

get "/admin/participants/:id/edit.json" do
  content_type :json
  Participant.find(params[:id]).to_json
end

put "/admin/participants/:id/update" do
puts params.inspect
  errors = participant_errors
  if errors.empty?
    p = Participant.find(params[:id])
    p.update_attributes({username: params[:username], email_address: params[:email_address],
      phone_number: params[:phone_number], test_user: (params[:test_user].blank? ? false : true)})
  end
  [200, {}, errors.join('<br>')]  
end

post '/admin/participants/create' do
  errors = participant_errors
  if errors.empty?
    Participant.create!({username: params[:username], email_address: params[:email_address],
      phone_number: params[:phone_number], test_user: (params[:test_user].blank? ? false : true)})
  end
  [200, {}, errors.join('<br>')]
end

def participant_errors
  errors = []
  if params[:username].blank?
    errors << I18n.t('errors.name_required')
  end
  if params[:phone_number].blank? and params[:email_address].blank?
    errors << I18n.t('errors.phone_or_email_required')
  end
  errors  
end

get '/admin/notifications' do
  @setting = Setting.first
  haml :notifications
end

post '/admin/change_notifications' do
  if params[:email_notification].blank? or params[:sms_notification].blank? 
    flash[:error] = I18n.t('errors.notification_text')
  else
    @setting = Setting.first
    @setting.update_attributes({sms_notification: params[:sms_notification],
      email_notification: params[:email_notification], email_subject: params[:email_subject]})
    flash[:notice] = I18n.t('notices.changes_saved')
  end
  redirect to i18n_link('/admin/notifications')
end

post '/admin/clear_log' do
  AlarmLogs.clear
#  flash[:notice] = I18n.t('settings.log_cleared')
  [200, {}, []]
end

get '/logout' do
  session.delete(:identity)
  flash[:notice] = I18n.t('notices.logged_out')
  redirect to '/'
end
