# see: http://smherwig.blogspot.de/2013/05/a-simple-binascii-module-in-ruby-and-lua.html
module Binascii
  def self.hexlify(s)
    a = []
    s.each_byte do |b|
      a << sprintf('%02x', b)
    end
    a.join
  end
 
  def self.unhexlify(s)
    a = s.split
    return a.pack('H*')
  end
end
