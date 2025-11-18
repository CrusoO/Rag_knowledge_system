"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { MessageSquare, Upload, Settings, PlusCircle, Trash2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"

interface Conversation {
  id: string
  title: string
  updatedAt: Date
}

interface SidebarProps {
  conversations: Conversation[]
  onNewChat: () => void
  onDeleteConversation: (id: string) => void
}

export function Sidebar({ conversations, onNewChat, onDeleteConversation }: SidebarProps) {
  const pathname = usePathname()

  return (
    <div className="flex h-full w-64 flex-col border-r bg-background">
      <div className="p-4">
        <Button onClick={onNewChat} className="w-full" size="sm">
          <PlusCircle className="mr-2 h-4 w-4" />
          New Chat
        </Button>
      </div>

      <Separator />

      <nav className="flex-1 space-y-1 p-2">
        <Link href="/dashboard">
          <Button
            variant={pathname === "/dashboard" ? "secondary" : "ghost"}
            className="w-full justify-start"
            size="sm"
          >
            <MessageSquare className="mr-2 h-4 w-4" />
            Chat
          </Button>
        </Link>
        <Link href="/documents">
          <Button
            variant={pathname === "/documents" ? "secondary" : "ghost"}
            className="w-full justify-start"
            size="sm"
          >
            <Upload className="mr-2 h-4 w-4" />
            Documents
          </Button>
        </Link>
        <Link href="/settings">
          <Button
            variant={pathname === "/settings" ? "secondary" : "ghost"}
            className="w-full justify-start"
            size="sm"
          >
            <Settings className="mr-2 h-4 w-4" />
            Settings
          </Button>
        </Link>
      </nav>

      <Separator />

      <div className="flex-1 overflow-hidden">
        <div className="p-2">
          <h3 className="mb-2 px-2 text-xs font-semibold text-muted-foreground">
            Recent Conversations
          </h3>
        </div>
        <ScrollArea className="h-[calc(100vh-300px)]">
          <div className="space-y-1 p-2">
            {conversations.map((conversation) => (
              <div
                key={conversation.id}
                className="group flex items-center justify-between rounded-lg p-2 hover:bg-accent"
              >
                <Link
                  href={`/chat/${conversation.id}`}
                  className="flex-1 truncate text-sm"
                >
                  {conversation.title}
                </Link>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 opacity-0 group-hover:opacity-100"
                  onClick={() => onDeleteConversation(conversation.id)}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>
    </div>
  )
}

