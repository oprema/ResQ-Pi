require 'digest'
require 'sinatra/activerecord'
require './binascii'

ActiveRecord::Base.establish_connection(
  adapter: 'sqlite3',
  database:  '/home/pi/.resq-pi/resq-pi.db'
)

class Setting < ActiveRecord::Base
  def initialize
    @setting ||= Setting.first
  end

  def password_ok?(access_code)
    #puts ActiveRecord::Base.connection.tables
    return false if @setting.nil?

    sha256 = Digest::SHA256.new
    if Binascii.hexlify(sha256.digest(@setting.salt + access_code)) == @setting.access_token
      return true
    end
    false
  end

  def change_password(old_password, new_password)
    if password_ok?(old_password)
      salt = SecureRandom.hex(32) # add a 256bit salt
      sha256 = Digest::SHA256.new
   
      access_token =Binascii.hexlify(sha256.digest(salt + new_password))
      @setting.update_attributes({salt: salt, access_token: access_token, updated_at: Time.now})
      return true
    end
    false
  end

  def identity
    @setting.username || "Admin"
  end
end

class ResqLog < ActiveRecord::Base
  def self.clear
    ResqLogs.delete_all
  end
end


class Participant < ActiveRecord::Base
  def self.sms
    Participant.where("phone_number IS NOT NULL and phone_number IS NOT ''")
  end

  def self.email
    Participant.where("email_address IS NOT NULL and email_address IS NOT ''")
  end

  def self.sms_list
    participants = self.sms.select do |p|
      p.username = p.test_user > 0 ? "<span class=\"green\">#{p.username}</span>" : p.username
    end
    list = participants.map(&:username).join(", ")
    list.blank? ? "No SMS participants" : list
  end

  def self.email_list
    participants = self.email.select do |p|
      p.username = p.test_user > 0 ? "<span class=\"green\">#{p.username}</span>" : p.username
    end
    list = participants.map(&:username).join(", ")
    list.blank? ? "No E-Mail participants" : list
  end  
end

class AlarmLog < ActiveRecord::Base
end
