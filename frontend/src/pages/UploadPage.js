import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, FileText, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import LoadingScreen from "./LoadingScreen";
import axios from "axios";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const UploadPage = () => {
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const uploadedFile = e.dataTransfer.files[0];
      if (uploadedFile.name.endsWith(".pdf") || uploadedFile.name.endsWith(".docx")) {
        setFile(uploadedFile);
      } else {
        toast.error("Please upload a PDF or DOCX file");
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const uploadedFile = e.target.files[0];
      if (uploadedFile.name.endsWith(".pdf") || uploadedFile.name.endsWith(".docx")) {
        setFile(uploadedFile);
      } else {
        toast.error("Please upload a PDF or DOCX file");
      }
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await axios.post(`${API}/upload-resume`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      if (response.data.success) {
        // Navigate to results with data
        navigate("/results", {
          state: {
            userSkills: response.data.user_skills,
            careerMatches: response.data.career_matches,
          },
        });
      }
    } catch (error) {
      console.error("Error analyzing resume:", error);
      toast.error(error.response?.data?.detail || "Failed to analyze resume");
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingScreen />;
  }

  return (
    <div className="min-h-screen relative overflow-hidden" style={{ background: 'linear-gradient(135deg, #e0f2f1 0%, #b2dfdb 50%, #80cbc4 100%)' }}>
      {/* Header */}
      <nav className="glass" style={{ borderBottom: '1px solid rgba(255,255,255,0.2)' }}>
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-7 h-7" style={{ color: '#00695c' }} />
            <h1 className="text-2xl font-bold" style={{ color: '#004d40' }}>NextStepAI</h1>
          </div>
          <Button
            data-testid="admin-dashboard-link"
            variant="ghost"
            onClick={() => navigate('/admin')}
            className="hover:bg-white/50"
          >
            Admin Dashboard
          </Button>
        </div>
      </nav>

      {/* Main Content */}
      <div className="flex items-center justify-center min-h-[calc(100vh-80px)] px-6 py-12">
        <div className="w-full max-w-2xl fade-in">
          {/* Hero Text */}
          <div className="text-center mb-12">
            <h1
              data-testid="main-heading"
              className="text-5xl sm:text-6xl font-bold mb-6"
              style={{ color: '#004d40', lineHeight: '1.1' }}
            >
              Your Future, Demystified.
            </h1>
            <p
              data-testid="sub-heading"
              className="text-lg sm:text-xl"
              style={{ color: '#00695c' }}
            >
              Upload your resume to receive a personalized career roadmap,
              skill-gap analysis, and direct learning paths.
            </p>
          </div>

          {/* Upload Card */}
          <div
            className="glass rounded-2xl p-8 shadow-xl"
            style={{ boxShadow: '0 20px 60px rgba(0, 0, 0, 0.1)' }}
          >
            <div
              data-testid="file-upload-area"
              className={`border-3 border-dashed rounded-xl p-12 text-center transition-all ${
                dragActive ? 'border-teal-600 bg-teal-50' : 'border-gray-300 bg-white/30'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              style={{ cursor: 'pointer' }}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx"
                onChange={handleFileChange}
                className="hidden"
                data-testid="file-input"
              />

              {!file ? (
                <div className="flex flex-col items-center gap-4">
                  <Upload className="w-16 h-16" style={{ color: '#00897b' }} />
                  <div>
                    <p className="text-lg font-semibold mb-2" style={{ color: '#004d40' }}>
                      Drag and drop your resume here
                    </p>
                    <p className="text-sm" style={{ color: '#00695c' }}>
                      Supports .PDF and .DOCX files
                    </p>
                  </div>
                  <Button
                    data-testid="browse-files-button"
                    variant="outline"
                    className="mt-2"
                    style={{
                      borderColor: '#00897b',
                      color: '#00897b',
                    }}
                  >
                    Or Browse Files
                  </Button>
                </div>
              ) : (
                <div className="flex items-center justify-center gap-4">
                  <FileText className="w-12 h-12" style={{ color: '#00897b' }} />
                  <div className="text-left">
                    <p className="font-semibold" style={{ color: '#004d40' }}>
                      {file.name}
                    </p>
                    <p className="text-sm" style={{ color: '#00695c' }}>
                      {(file.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                  <Button
                    data-testid="remove-file-button"
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      setFile(null);
                    }}
                    className="ml-auto"
                  >
                    Remove
                  </Button>
                </div>
              )}
            </div>

            <Button
              data-testid="analyze-resume-button"
              disabled={!file}
              onClick={handleAnalyze}
              className="w-full mt-6 py-6 text-lg font-semibold rounded-xl"
              style={{
                background: file ? 'linear-gradient(135deg, #00897b 0%, #00695c 100%)' : '#ccc',
                color: 'white',
                boxShadow: file ? '0 10px 30px rgba(0, 137, 123, 0.3)' : 'none',
              }}
            >
              Analyze My Resume
            </Button>
          </div>

          {/* Info Section */}
          <div className="mt-8 text-center">
            <p className="text-sm" style={{ color: '#00695c' }}>
              Your data is processed securely and never shared with third parties.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadPage;
