# GitHub "workflow" scope token + owner, for the Cloudflare Worker.
# Create: github.com/settings/personal-access-tokens/new (fine-grained)
#   - Repository access: Only select repositories -> imzyrix/imzyrix
#   - Permissions -> Actions: Read and write
# Store the token in the WORKER (not the repo):
#   npx wrangler secret put GH_TOKEN
