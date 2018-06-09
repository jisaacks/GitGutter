build_release:
	./release build

release:
	build_release
	./release publish --token `cat $HOME/.github_access_token`

build_docs:
	mkdocs

publish_docs:
	mkdocs gh-deploy
