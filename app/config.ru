require 'rubygems'
require 'sinatra'
require 'rack'
require 'rack/contrib'
require './app'

require File.expand_path '../app.rb', __FILE__
use Rack::Locale

run Sinatra::Application
