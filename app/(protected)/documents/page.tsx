"use client"

import { useState, useEffect } from "react"
import axios from "axios"
import { FileText, Trash2, CheckCircle, Clock, AlertCircle } from "lucide-react"

import { FileUploader } from "@/components/file-uploader"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useToast } from "@/components/ui/use-toast"
import { formatBytes, formatDate } from "@/lib/utils"

interface Document {
  id: string
  filename: string
  originalName: string
  fileType: string
  fileSize: number
  status: string
  chunks: number
  uploadedAt: Date
  processedAt?: Date
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const { toast } = useToast()

  const loadDocuments = async () => {
    try {
      const response = await axios.get("/api/documents")
      setDocuments(response.data)
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load documents",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadDocuments()
  }, [])

  const handleDelete = async (id: string) => {
    try {
      await axios.delete(`/api/documents/${id}`)
      setDocuments((prev) => prev.filter((doc) => doc.id !== id))
      toast({
        title: "Success",
        description: "Document deleted successfully",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete document",
        variant: "destructive",
      })
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case "processing":
        return <Clock className="h-5 w-5 text-yellow-500" />
      case "failed":
        return <AlertCircle className="h-5 w-5 text-red-500" />
      default:
        return <Clock className="h-5 w-5 text-gray-500" />
    }
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Documents</h1>
          <p className="text-muted-foreground mt-1">
            Upload and manage your knowledge base documents
          </p>
        </div>

        <FileUploader onUploadComplete={loadDocuments} />

        <Card>
          <CardHeader>
            <CardTitle>Your Documents</CardTitle>
            <CardDescription>
              {documents.length} document{documents.length !== 1 ? "s" : ""} uploaded
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <p className="text-center text-muted-foreground py-8">Loading...</p>
            ) : documents.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">
                No documents uploaded yet
              </p>
            ) : (
              <div className="space-y-3">
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    className="flex items-center gap-4 rounded-lg border p-4"
                  >
                    <FileText className="h-8 w-8 text-muted-foreground" />
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{doc.originalName}</p>
                        {getStatusIcon(doc.status)}
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span>{formatBytes(doc.fileSize)}</span>
                        <span>{doc.fileType.toUpperCase()}</span>
                        <span>{doc.chunks} chunks</span>
                        <span>{formatDate(doc.uploadedAt)}</span>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(doc.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

