import { NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth"
import { prisma } from "@/lib/prisma"

const RATE_LIMIT_WINDOW = 15 * 60 * 1000
const MAX_REQUESTS = 100

export async function checkRateLimit(endpoint: string): Promise<boolean> {
  const session = await getServerSession(authOptions)

  if (!session?.user?.id) {
    return false
  }

  const userId = session.user.id
  const now = new Date()
  const windowStart = new Date(now.getTime() - RATE_LIMIT_WINDOW)

  const rateLimit = await prisma.rateLimit.findUnique({
    where: {
      userId_endpoint: {
        userId,
        endpoint,
      },
    },
  })

  if (!rateLimit) {
    await prisma.rateLimit.create({
      data: {
        userId,
        endpoint,
        count: 1,
        windowStart: now,
      },
    })
    return true
  }

  if (rateLimit.windowStart < windowStart) {
    await prisma.rateLimit.update({
      where: {
        userId_endpoint: {
          userId,
          endpoint,
        },
      },
      data: {
        count: 1,
        windowStart: now,
      },
    })
    return true
  }

  if (rateLimit.count >= MAX_REQUESTS) {
    return false
  }

  await prisma.rateLimit.update({
    where: {
      userId_endpoint: {
        userId,
        endpoint,
      },
    },
    data: {
      count: {
        increment: 1,
      },
    },
  })

  return true
}

