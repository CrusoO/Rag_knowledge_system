import { NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth"
import { prisma } from "@/lib/prisma"

export async function GET() {
  try {
    const session = await getServerSession(authOptions)

    if (!session?.user || session.user.role !== "admin") {
      return NextResponse.json({ message: "Forbidden" }, { status: 403 })
    }

    const totalUsers = await prisma.user.count()
    const totalDocuments = await prisma.document.count()
    const totalConversations = await prisma.conversation.count()
    const totalMessages = await prisma.message.count()

    const documentsPerDay = await prisma.$queryRaw<
      Array<{ date: string; count: bigint }>
    >`
      SELECT 
        DATE(uploaded_at) as date,
        COUNT(*) as count
      FROM "Document"
      WHERE uploaded_at >= NOW() - INTERVAL '30 days'
      GROUP BY DATE(uploaded_at)
      ORDER BY date DESC
    `

    const messagesPerDay = await prisma.$queryRaw<
      Array<{ date: string; count: bigint }>
    >`
      SELECT 
        DATE(created_at) as date,
        COUNT(*) as count
      FROM "Message"
      WHERE created_at >= NOW() - INTERVAL '30 days'
      GROUP BY DATE(created_at)
      ORDER BY date DESC
    `

    return NextResponse.json({
      totalUsers,
      totalDocuments,
      totalConversations,
      totalMessages,
      documentsPerDay: documentsPerDay.map((d) => ({
        date: d.date,
        count: Number(d.count),
      })),
      messagesPerDay: messagesPerDay.map((m) => ({
        date: m.date,
        count: Number(m.count),
      })),
    })
  } catch (error) {
    console.error("Error fetching analytics:", error)
    return NextResponse.json(
      { message: "Internal server error" },
      { status: 500 }
    )
  }
}

