import { setupServer } from 'msw/node'
import { handlers } from './handlers'

// Setup MSW server for Node.js environment (testing)
export const server = setupServer(...handlers)

// Start server and handle errors
server.listen({ onUnhandledRequest: 'error' })