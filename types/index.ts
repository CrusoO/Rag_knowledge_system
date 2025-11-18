export interface Document {
  id: string
  userId: string
  filename: string
  originalName: string
  fileType: string
  fileSize: number
  status: string
  chunks: number
  uploadedAt: Date
  processedAt?: Date
  error?: string
}

export interface Conversation {
  id: string
  userId: string
  title: string
  createdAt: Date
  updatedAt: Date
  messages: Message[]
}

export interface Message {
  id: string
  conversationId: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  createdAt: Date
}

export interface Source {
  documentId: string
  documentName: string
  chunk: string
  score: number
}

export interface ChatRequest {
  conversationId?: string
  message: string
}

export interface ChatResponse {
  conversationId: string
  message: Message
}

export interface UploadResponse {
  documentId: string
  filename: string
  status: string
}

export interface Analytics {
  totalUsers: number
  totalDocuments: number
  totalConversations: number
  totalMessages: number
  documentsPerDay: { date: string; count: number }[]
  messagesPerDay: { date: string; count: number }[]
}

