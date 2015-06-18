TOKEN="`cat $HOME/.github_access_token`"
VERSION="`cat ./release_messages/dest/VERSION`"
PRE_RELEASE="`cat ./release_messages/dest/PRE_RELEASE`"
SHA="`git rev-parse HEAD`"
API_JSON=$(printf '{"tag_name": "%s","prerelease": %s,"target_commitish": "%s"}' "$VERSION" "$PRE_RELEASE" "$SHA")
API_ENDPOINT=$(printf 'https://api.github.com/repos/jisaacks/GitGutter/releases?access_token=%s' "$TOKEN")
curl --data "$API_JSON" "$API_ENDPOINT"
echo "\033[0;32mCreated\033[0m release \033[1;33m$VERSION\033[0m"
echo "\033[1;32mDone.\033[0m"
