/**
 * Deployed on Vercel as /api/trigger.
 * Holds the GitHub token server-side (never exposed to the browser) and
 * fires the same workflow your cron schedule uses, via workflow_dispatch.
 *
 * Set these in Vercel project settings -> Environment Variables:
 *   GITHUB_TOKEN   - a fine-grained PAT with "Actions: write" on this repo
 *   GITHUB_OWNER   - your github username
 *   GITHUB_REPO    - stock-agent (or whatever you named the repo)
 */
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).send('Use POST');
  }

  const { GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO } = process.env;
  if (!GITHUB_TOKEN || !GITHUB_OWNER || !GITHUB_REPO) {
    return res.status(500).send('Server missing GITHUB_TOKEN / GITHUB_OWNER / GITHUB_REPO env vars');
  }

  const url = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/actions/workflows/scheduled-screen.yml/dispatches`;

  const ghRes = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github+json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ ref: 'main' }),
  });

  if (ghRes.status === 204) {
    return res.status(200).json({ status: 'triggered' });
  }

  const text = await ghRes.text();
  return res.status(502).send(`GitHub API error: ${ghRes.status} ${text}`);
}
