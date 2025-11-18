"use client"

import { useCallback, useState } from "react"
import { useDropzone } from "react-dropzone"
import { Upload, File, X, CheckCircle, AlertCircle } from "lucide-react"
import axios from "axios"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { useToast } from "@/components/ui/use-toast"
import { formatBytes } from "@/lib/utils"

interface UploadedFile {
  file: File
  status: "pending" | "uploading" | "success" | "error"
  progress: number
  error?: string
}

export function FileUploader({ onUploadComplete }: { onUploadComplete?: () => void }) {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const { toast } = useToast()

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map((file) => ({
      file,
      status: "pending" as const,
      progress: 0,
    }))
    setFiles((prev) => [...prev, ...newFiles])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "text/plain": [".txt"],
      "text/markdown": [".md"],
    },
    maxSize: 10485760,
  })

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const uploadFile = async (index: number) => {
    const fileToUpload = files[index]
    if (!fileToUpload) return

    setFiles((prev) =>
      prev.map((f, i) =>
        i === index ? { ...f, status: "uploading" as const, progress: 0 } : f
      )
    )

    const formData = new FormData()
    formData.append("file", fileToUpload.file)

    try {
      const response = await axios.post("/api/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        onUploadProgress: (progressEvent) => {
          const progress = progressEvent.total
            ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
            : 0
          setFiles((prev) =>
            prev.map((f, i) => (i === index ? { ...f, progress } : f))
          )
        },
      })

      setFiles((prev) =>
        prev.map((f, i) =>
          i === index ? { ...f, status: "success" as const, progress: 100 } : f
        )
      )

      toast({
        title: "Upload successful",
        description: `${fileToUpload.file.name} has been uploaded and is being processed.`,
      })

      if (onUploadComplete) {
        onUploadComplete()
      }
    } catch (error) {
      setFiles((prev) =>
        prev.map((f, i) =>
          i === index
            ? {
                ...f,
                status: "error" as const,
                error: "Upload failed. Please try again.",
              }
            : f
        )
      )

      toast({
        title: "Upload failed",
        description: "There was an error uploading your file. Please try again.",
        variant: "destructive",
      })
    }
  }

  const uploadAll = async () => {
    for (let i = 0; i < files.length; i++) {
      if (files[i].status === "pending") {
        await uploadFile(i)
      }
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="pt-6">
          <div
            {...getRootProps()}
            className={`cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
              isDragActive
                ? "border-primary bg-primary/5"
                : "border-muted-foreground/25 hover:border-primary/50"
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
            <p className="mt-2 text-sm font-medium">
              Drag & drop files here, or click to select
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Supports PDF, TXT, MD files up to 10MB
            </p>
          </div>
        </CardContent>
      </Card>

      {files.length > 0 && (
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium">Files ({files.length})</h3>
                <Button
                  size="sm"
                  onClick={uploadAll}
                  disabled={!files.some((f) => f.status === "pending")}
                >
                  Upload All
                </Button>
              </div>

              {files.map((uploadedFile, index) => (
                <div
                  key={index}
                  className="flex items-center gap-3 rounded-lg border p-3"
                >
                  <File className="h-8 w-8 text-muted-foreground" />
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium truncate">
                        {uploadedFile.file.name}
                      </p>
                      <div className="flex items-center gap-2">
                        {uploadedFile.status === "success" && (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        )}
                        {uploadedFile.status === "error" && (
                          <AlertCircle className="h-4 w-4 text-red-500" />
                        )}
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6"
                          onClick={() => removeFile(index)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {formatBytes(uploadedFile.file.size)}
                    </p>
                    {uploadedFile.status === "uploading" && (
                      <Progress value={uploadedFile.progress} className="h-1" />
                    )}
                    {uploadedFile.status === "error" && (
                      <p className="text-xs text-red-500">{uploadedFile.error}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

