import { NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth"
import { prisma } from "@/lib/prisma"
import axios from "axios"

export async function POST(request: Request) {
  try {
    const session = await getServerSession(authOptions)

    if (!session?.user) {
      return NextResponse.json({ message: "Unauthorized" }, { status: 401 })
    }

    const { conversationId, message } = await request.json()

    if (!message) {
      return NextResponse.json({ message: "Message is required" }, { status: 400 })
    }

    let conversation
    if (conversationId) {
      conversation = await prisma.conversation.findUnique({
        where: { id: conversationId },
      })

      if (conversation?.userId !== session.user.id) {
        return NextResponse.json({ message: "Forbidden" }, { status: 403 })
      }
    } else {
      conversation = await prisma.conversation.create({
        data: {
          userId: session.user.id,
          title: message.substring(0, 50),
        },
      })
    }

    await prisma.message.create({
      data: {
        conversationId: conversation.id,
        role: "user",
        content: message,
      },
    })

    const backendUrl = process.env.BACKEND_API_URL || "http://localhost:8000"
    
    let assistantResponse
    try {
      const response = await axios.post(`${backendUrl}/api/chat`, {
        userId: session.user.id,
        message,
      })

      assistantResponse = response.data
    } catch (error) {
      console.error("Backend chat error:", error)
      assistantResponse = {
        content: "I apologize, but I'm having trouble processing your request right now. Please try again later.",
        sources: [],
      }
    }

    const assistantMessage = await prisma.message.create({
      data: {
        conversationId: conversation.id,
        role: "assistant",
        content: assistantResponse.content,
        sources: assistantResponse.sources || [],
      },
    })

    await prisma.conversation.update({
      where: { id: conversation.id },
      data: { updatedAt: new Date() },
    })

    return NextResponse.json({
      conversationId: conversation.id,
      message: assistantMessage,
    })
  } catch (error) {
    console.error("Chat error:", error)
    return NextResponse.json(
      { message: "Internal server error" },
      { status: 500 }
    )
  }
}

