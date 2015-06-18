#!/usr/bin/ruby

require "fileutils"
require "json"

json = {}

# Get messages in src in the correct order
files = Dir.glob(File.join(%w{release_messages src messages *.txt})).sort_by do |file|
  name = File.basename(file, '.txt')
  if name == 'install'
    [0, 0, 0, 0]
  else
    if name =~ /^(.*)-pre(.*)/
      name = $1.split('.').map(&:to_i).push(0).push($2)
    else
      name.split('.').map(&:to_i).push(1)
    end
  end
end

# Grab the global message
global_message = File.read(File.join(%w{release_messages src global_message.txt}))

# Remove previous build
FileUtils.rm_rf(File.join(%w{release_messages dest .}), secure: true)
puts "\033[0;31mDeleted\033[0m #{File.join(%w{release_messages dest *})}"

# Write the files
files.each do |file|
  contents = File.read(file)
  path = File.join(%w{release_messages dest}.push(File.basename(file)))
  name = File.basename(path, ".txt")
  json[name] = path
  msg = "\033[0;32mCreated\033[0m #{path}"
  if file == files.last || file == files.first
    msg += "\033[1;35m (with global message)\033[0m"
    contents += "\n\n" unless contents.empty?
    contents += global_message
    if file == files.last
      File.write(File.join(%w{release_messages dest VERSION}), name)
      File.write(File.join(%w{release_messages dest PRE_RELEASE}), !!(name =~ /pre/))
    end
  end
  File.write(path, contents)
  puts msg
end

File.write("messages.json", JSON.pretty_generate(json))
puts "\033[0;32mCreated\033[0m messages.json"

puts "\033[1;32mDone.\033[0m"
