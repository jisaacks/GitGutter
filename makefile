build_release:
	./release_messages/src/build.rb

release: build_release
	./release_messages/src/release.sh
