build_release:
	./release build

release:
	build_release
	./release publish --token `cat $HOME/.github_access_token`
