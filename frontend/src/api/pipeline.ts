import client from './client'

export async function triggerFetchRss() {
  const resp = await client.post('/pipeline/fetch-rss')
  return resp.data
}

export async function triggerProcessNews() {
  const resp = await client.post('/pipeline/process-news')
  return resp.data
}

export async function triggerCheckSimilarity() {
  const resp = await client.post('/pipeline/check-similarity')
  return resp.data
}

export async function triggerJudgeImportance() {
  const resp = await client.post('/pipeline/judge-importance')
  return resp.data
}

export async function triggerFullPipeline() {
  const resp = await client.post('/pipeline/run-full')
  return resp.data
}
