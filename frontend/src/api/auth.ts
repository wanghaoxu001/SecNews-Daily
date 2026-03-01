import client from './client'
import type { LoginRequest, TokenResponse } from '../types'

export async function login(data: LoginRequest): Promise<TokenResponse> {
  const resp = await client.post<TokenResponse>('/auth/login', data)
  return resp.data
}
