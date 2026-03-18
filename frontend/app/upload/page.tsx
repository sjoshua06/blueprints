'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import FileUploadBox from '@/components/file-upload-box';

export default function UploadPage() {
  const [bomFile, setBomFile] = useState<File | null>(null);
  const [receiptFile, setReceiptFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const router = useRouter();

  const handleAnalyze = async () => {
    if (!bomFile || !receiptFile) return;

    setAnalyzing(true);
    // Simulate analysis
    setTimeout(() => {
      router.push('/dashboard');
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="flex items-center justify-between px-6 py-4 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-lg">⚡</span>
          </div>
          <span className="text-xl font-bold text-foreground">ChainAI</span>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/3 right-0 w-96 h-96 bg-primary/20 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-1/4 w-96 h-96 bg-accent/10 rounded-full blur-3xl"></div>
        </div>

        <div className="relative z-10">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-foreground mb-2">Upload Your Files</h1>
            <p className="text-foreground/60">Submit your Bill of Materials (BOM) and Supplier Receipt documents to analyze supply chain risks</p>
          </div>

          <div className="grid md:grid-cols-2 gap-6 mb-8">
            <FileUploadBox
              title="Bill of Materials (BOM)"
              description="Upload your BOM CSV or Excel file"
              file={bomFile}
              onChange={setBomFile}
              accept=".csv,.xlsx,.xls"
            />
            
            <FileUploadBox
              title="Supplier Receipt"
              description="Upload your receipt PDF or Excel file"
              file={receiptFile}
              onChange={setReceiptFile}
              accept=".pdf,.xlsx,.xls"
            />
          </div>

          {/* Analysis Info Card */}
          <Card className="bg-card/50 border-border mb-8">
            <CardHeader>
              <CardTitle className="text-lg">What We Analyze</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-foreground/80">
                <li className="flex items-start gap-3">
                  <span className="text-primary font-bold mt-1">•</span>
                  <span><strong>Internal Risk:</strong> Component quality and performance metrics</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-primary font-bold mt-1">•</span>
                  <span><strong>Compatibility:</strong> Cross-component compatibility verification</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-primary font-bold mt-1">•</span>
                  <span><strong>Supplier Risk:</strong> Supplier reliability and compliance rating</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="flex gap-4">
            <Button
              size="lg"
              disabled={!bomFile || !receiptFile || analyzing}
              onClick={handleAnalyze}
              className="bg-primary hover:bg-primary/90 flex-1"
            >
              {analyzing ? 'Analyzing Files...' : 'Analyze Supply Chain'}
            </Button>
            <Button size="lg" variant="outline">
              Clear Files
            </Button>
          </div>

          {/* Loading Animation */}
          {analyzing && (
            <div className="mt-8 text-center">
              <div className="inline-flex items-center justify-center">
                <div className="relative w-12 h-12">
                  <div className="absolute inset-0 border-4 border-primary/20 rounded-full"></div>
                  <div className="absolute inset-0 border-4 border-transparent border-t-primary rounded-full animate-spin"></div>
                </div>
              </div>
              <p className="mt-4 text-foreground/60">Processing your documents...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
