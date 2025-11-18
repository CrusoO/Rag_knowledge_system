import { NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth"
import { prisma } from "@/lib/prisma"
import { writeFile, mkdir } from "fs/promises"
import path from "path"
import axios from "axios"

export async function POST(request: Request) {
  try {
    const session = await getServerSession(authOptions)

    if (!session?.user) {
      return NextResponse.json({ message: "Unauthorized" }, { status: 401 })
    }

    const formData = await request.formData()
    const file = formData.get("file") as File

    if (!file) {
      return NextResponse.json({ message: "No file provided" }, { status: 400 })
    }

    const bytes = await file.arrayBuffer()
    const buffer = Buffer.from(bytes)

    const uploadsDir = path.join(process.cwd(), "uploads")
    await mkdir(uploadsDir, { recursive: true })

    const filename = `${Date.now()}-${file.name}`
    const filepath = path.join(uploadsDir, filename)

    await writeFile(filepath, buffer)

    const document = await prisma.document.create({
      data: {
        userId: session.user.id,
        filename,
        originalName: file.name,
        fileType: file.type,
        fileSize: file.size,
        status: "processing",
      },
    })

    const backendUrl = process.env.BACKEND_API_URL || "http://localhost:8000"
    
    try {
      await axios.post(`${backendUrl}/api/process-document`, {
        documentId: document.id,
        filename,
        filepath,
        userId: session.user.id,
      })
    } catch (error) {
      console.error("Failed to trigger backend processing:", error)
    }

    return NextResponse.json({
      documentId: document.id,
      filename: document.filename,
      status: document.status,
    })
  } catch (error) {
    console.error("Upload error:", error)
    return NextResponse.json(
      { message: "Internal server error" },
      { status: 500 }
    )
  }
}

