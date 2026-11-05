# GitHub from agents: `gh` commands and REST equivalents

Skills use the short `gh` commands, which work locally and in GitHub Actions. In **Claude Code cloud
sessions** (`CLAUDE_CODE_REMOTE=true`), GitHub **GraphQL is blocked**, and most `gh issue …`,
`gh pr …` and `gh label list` subcommands are GraphQL-based. There, use the REST forms below. They work
everywhere. `{owner}/{repo}` placeholders are filled in by `gh api` from the current checkout.

| Task | Short form (local / Actions) | REST form (works everywhere) |
|---|---|---|
| View issue | `gh issue view N --comments` | `gh api repos/{owner}/{repo}/issues/N --jq '{title,state,body,labels:[.labels[].name]}'` + `gh api repos/{owner}/{repo}/issues/N/comments --jq '.[] \| {user:.user.login,body}'` |
| List open issues | `gh issue list` | `gh api 'repos/{owner}/{repo}/issues?state=open&per_page=50' --jq '.[] \| select(.pull_request\|not) \| "\(.number)\t\(.title)"'` |
| Search issues (duplicates) | `gh issue list --search "terms"` | `gh api -X GET search/issues -f q='repo:{owner}/{repo} is:issue terms' --jq '.items[] \| "\(.number)\t\(.title)"'` |
| Create issue | `gh issue create --title T --body-file F --label L` | `gh api repos/{owner}/{repo}/issues -f title='T' -F body=@F -f 'labels[]=L'` |
| Add labels | `gh issue edit N --add-label L` | `gh api repos/{owner}/{repo}/issues/N/labels -f 'labels[]=L'` |
| Comment on issue or PR | `gh issue comment N --body-file F` / `gh pr comment N --body-file F` | `gh api repos/{owner}/{repo}/issues/N/comments -F body=@F` |
| List labels | `gh label list` | `gh api 'repos/{owner}/{repo}/labels?per_page=100' --jq '.[].name'` |
| View PR | `gh pr view N` | `gh api repos/{owner}/{repo}/pulls/N --jq '{title,body,state,head:.head.ref,base:.base.ref}'` |
| PR diff · files | `gh pr diff N` | `gh api repos/{owner}/{repo}/pulls/N -H 'Accept: application/vnd.github.diff'` · `gh api repos/{owner}/{repo}/pulls/N/files --jq '.[].filename'` |
| Create PR | `gh pr create --base main --head B --title T --body-file F` | `gh api repos/{owner}/{repo}/pulls -f base=main -f head=B -f title='T' -F body=@F` (add `-F draft=true`) |
| PR checks | `gh pr checks N` | `gh api repos/{owner}/{repo}/commits/SHA/check-runs --jq '.check_runs[] \| "\(.name)\t\(.status)\t\(.conclusion)"'` |
| Review comments | `gh api graphql …` (reviewThreads) | Inline comments: `gh api repos/{owner}/{repo}/pulls/N/comments`. Reviews: `…/pulls/N/reviews`. Cloud sessions also offer `GET repos/{owner}/{repo}/pulls/N/ccr/review_threads` |
| Reply to a review comment | — | `gh api repos/{owner}/{repo}/pulls/N/comments/COMMENT_ID/replies -f body='…'` |
| Resolve a thread | GraphQL `resolveReviewThread` | Cloud sessions: `gh api -X POST repos/{owner}/{repo}/pulls/N/ccr/comments/COMMENT_ID/resolve` |
| Workflow runs and logs | `gh run list` · `gh run view ID --log-failed` | Already REST; works everywhere |

Notes:

- `gh run …`, `gh release …` and `gh label create` are REST-based and work in cloud sessions.
- Writes (create, comment, label) are outward-facing. Skills ask or confirm as their steps describe.
