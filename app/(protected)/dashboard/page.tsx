"use client"

import { useState, useEffect } from "react"
import { useSession } from "next-auth/react"
import axios from "axios"

import { Sidebar } from "@/components/sidebar"
import { ChatWindow } from "@/components/chat-window"
import { useToast } from "@/components/ui/use-toast"

interface Conversation {
  id: string
  title: string
  updatedAt: Date
}

interface Message {
  id: string
  conversationId: string
  role: "user" | "assistant"
  content: string
  sources?: any[]
  createdAt: Date
}

export default function DashboardPage() {
  const { data: session } = useSession()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConversation, setCurrentConversation] = useState<string | undefined>()
  const [messages, setMessages] = useState<Message[]>([])
  const { toast } = useToast()

  useEffect(() => {
    loadConversations()
  }, [])

  const loadConversations = async () => {
    try {
      const response = await axios.get("/api/conversations")
      setConversations(response.data)
    } catch (error) {
      console.error("Failed to load conversations:", error)
    }
  }

  const handleNewChat = async () => {
    setCurrentConversation(undefined)
    setMessages([])
  }

  const handleDeleteConversation = async (id: string) => {
    try {
      await axios.delete(`/api/conversations/${id}`)
      setConversations((prev) => prev.filter((c) => c.id !== id))
      if (currentConversation === id) {
        setCurrentConversation(undefined)
        setMessages([])
      }
      toast({
        title: "Success",
        description: "Conversation deleted",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete conversation",
        variant: "destructive",
      })
    }
  }

  const handleSendMessage = async (content: string) => {
    try {
      const response = await axios.post("/api/chat", {
        conversationId: currentConversation,
        message: content,
      })

      const { conversationId, message } = response.data

      if (!currentConversation) {
        setCurrentConversation(conversationId)
        loadConversations()
      }

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          conversationId,
          role: "user",
          content,
          createdAt: new Date(),
        },
        message,
      ])
    } catch (error) {
      throw error
    }
  }

  return (
    <div className="flex h-full">
      <Sidebar
        conversations={conversations}
        onNewChat={handleNewChat}
        onDeleteConversation={handleDeleteConversation}
      />
      <div className="flex-1">
        <ChatWindow
          conversationId={currentConversation}
          messages={messages}
          onSendMessage={handleSendMessage}
        />
      </div>
    </div>
  )
}

