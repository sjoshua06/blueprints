'use client';

import { useRef, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface FileUploadBoxProps {
  title: string;
  description: string;
  file: File | null;
  onChange: (file: File | null) => void;
  accept?: string;
}

export default function FileUploadBox({
  title,
  description,
  file,
  onChange,
  accept = '*',
}: FileUploadBoxProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files && files[0]) {
      onChange(files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onChange(e.target.files[0]);
    }
  };

  return (
    <Card
      className={`cursor-pointer transition-all border-2 ${
        isDragging
          ? 'border-primary bg-primary/5'
          : 'border-border hover:border-primary/50'
      } ${file ? 'bg-card/50' : ''}`}
      onClick={() => inputRef.current?.click()}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>

      <CardContent>
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          onChange={handleFileSelect}
          className="hidden"
        />

        {file ? (
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 bg-primary/10 rounded-lg border border-primary/20">
              <div className="w-10 h-10 bg-primary/20 rounded flex items-center justify-center flex-shrink-0">
                <span className="text-primary font-bold">📄</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground truncate">{file.name}</p>
                <p className="text-xs text-foreground/60">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onChange(null);
                }}
                className="text-primary hover:text-primary/80 font-bold"
              >
                ✕
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-3 py-8 text-center">
            <div className="text-4xl">📁</div>
            <div>
              <p className="text-foreground font-medium">Drag and drop your file here</p>
              <p className="text-sm text-foreground/60">or click to browse</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
