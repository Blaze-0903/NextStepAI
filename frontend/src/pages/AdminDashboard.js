import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles, ArrowLeft, Lock, RefreshCw, CheckCircle, XCircle, TrendingUp, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import axios from "axios";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
// Use the correct /api prefix for all calls
const API = `${BACKEND_URL}/api`; 

const AdminDashboard = () => {
  const [authenticated, setAuthenticated] = useState(false);
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [pendingSkills, setPendingSkills] = useState([]);
  const [pendingRoles, setPendingRoles] = useState([]);
  const [obsoleteSkills, setObsoleteSkills] = useState([]); // <-- NEW STATE
  const navigate = useNavigate();

  useEffect(() => {
    if (authenticated) {
      fetchPendingUpdates();
    }
  }, [authenticated]);

  const handleLogin = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/admin/login`, { password });
      if (response.data.success) {
        setAuthenticated(true);
        toast.success("Login successful");
      } else {
        toast.error(response.data.detail || "Invalid password");
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Invalid password");
    }
    setLoading(false);
  };

  const fetchPendingUpdates = async () => {
    try {
      const response = await axios.get(`${API}/admin/pending-updates`);
      // --- NEW LOGIC TO SPLIT ALL PENDING UPDATES ---
      const allPending = response.data.pending_updates || [];
      
      setPendingSkills(allPending.filter(p => p.type === 'skill'));
      setPendingRoles(allPending.filter(p => p.type === 'role'));
      setObsoleteSkills(allPending.filter(p => p.type === 'review_obsolete')); // <-- NEW

    } catch (error) {
      console.error("Error fetching pending updates:", error);
      toast.error("Failed to load pending updates");
    }
  };

  const handleReview = async (updateId, decision) => {
    try {
      const response = await axios.post(`${API}/admin/review`, {
        update_id: updateId,
        decision: decision,
        reviewer_name: "Admin",
      });

      if (response.data.success) {
        toast.success(`Update ${decision}ed successfully`);
        fetchPendingUpdates(); // Refresh the list
      }
    } catch (error) {
      console.error("Error reviewing update:", error);
      toast.error("Failed to review update");
    }
  };

  const triggerOntologyUpdate = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/trigger-ontology-update`);
      toast.success("Ontology update triggered");
      // Give the backend a moment to run before fetching
      setTimeout(fetchPendingUpdates, 2000);
    } catch (error) {
      console.error("Error triggering update:", error);
      toast.error("Failed to trigger update");
    }
    setLoading(false);
  };

  // --- LOGIN FORM (No changes) ---
  if (!authenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #e0f2f1 0%, #b2dfdb 50%, #80cbc4 100%)' }}>
        <Card className="w-full max-w-md shadow-xl">
          <CardHeader className="text-center">
            <div className="flex justify-center mb-4">
              <Lock className="w-12 h-12" style={{ color: '#00897b' }} />
            </div>
            <CardTitle className="text-2xl" style={{ color: '#004d40' }}>Admin Dashboard</CardTitle>
            <CardDescription>Enter password to access ontology management</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Input
                data-testid="admin-password-input"
                type="password"
                placeholder="Enter admin password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
                className="w-full"
              />
              <Button
                data-testid="admin-login-button"
                onClick={handleLogin}
                disabled={loading || !password}
                className="w-full"
                style={{
                  background: 'linear-gradient(135deg, #00897b 0%, #00695c 100%)',
                  color: 'white',
                }}
              >
                {loading ? "Logging in..." : "Login"}
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate("/")}
                className="w-full"
              >
                Back to Home
              </Button>
              <p className="text-xs text-center" style={{ color: '#00695c' }}>
                Default password: nextstep2025
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // --- MAIN DASHBOARD (Updated) ---
  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #f5f7fa 0%, #e8f5e9 100%)' }}>
      {/* Header (No changes) */}
      <nav className="glass" style={{ borderBottom: '1px solid rgba(255,255,255,0.2)' }}>
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-7 h-7" style={{ color: '#00695c' }} />
            <h1 className="text-2xl font-bold" style={{ color: '#004d40' }}>NextStepAI Admin</h1>
          </div>
          <div className="flex items-center gap-4">
            <Button
              data-testid="trigger-update-button"
              onClick={triggerOntologyUpdate}
              disabled={loading}
              className="flex items-center gap-2"
              style={{
                background: 'linear-gradient(135deg, #00897b 0%, #00695c 100%)',
                color: 'white',
              }}
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Trigger Weekly Update
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate("/")}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Home
            </Button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="fade-in">
          {/* Stats (Updated with Obsolete Skills) */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <Card className="border-none shadow-lg">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Pending Skills</CardTitle>
                <TrendingUp className="w-4 h-4" style={{ color: '#00897b' }} />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold" style={{ color: '#004d40' }}>{pendingSkills.length}</div>
                <p className="text-xs" style={{ color: '#00695c' }}>New skills awaiting review</p>
              </CardContent>
            </Card>
            
            <Card className="border-none shadow-lg">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Pending Roles</CardTitle>
                <TrendingUp className="w-4 h-4" style={{ color: '#00897b' }} />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold" style={{ color: '#004d40' }}>{pendingRoles.length}</div>
                <p className="text-xs" style={{ color: '#00695c' }}>New roles awaiting review</p>
              </CardContent>
            </Card>
            
            {/* --- NEW STAT CARD --- */}
            <Card className="border-none shadow-lg" style={{ background: 'linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%)' }}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium" style={{ color: '#e65100' }}>Obsolete Skills</CardTitle>
                <AlertTriangle className="w-4 h-4" style={{ color: '#e65100' }} />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold" style={{ color: '#bf360c' }}>{obsoleteSkills.length}</div>
                <p className="text-xs" style={{ color: '#e65100' }}>Flagged for depreciation</p>
              </CardContent>
            </Card>
          </div>

          {/* --- NEW OBSOLETE SKILLS SECTION --- */}
          <Card className="mb-8 border-none shadow-lg" data-testid="obsolete-skills-section" style={{ borderColor: '#ffcc80' }}>
            <CardHeader>
              <CardTitle className="text-2xl flex items-center gap-2" style={{ color: '#bf360c' }}>
                <AlertTriangle />
                Obsolete Skills Review
              </CardTitle>
              <CardDescription>Skills flagged for low market frequency or being outdated.</CardDescription>
            </CardHeader>
            <CardContent>
              {obsoleteSkills.length === 0 ? (
                <p className="text-center py-8" style={{ color: '#757575' }}>No obsolete skills flagged</p>
              ) : (
                <div className="space-y-4">
                  {obsoleteSkills.map((item, index) => (
                    <Card key={index} className="border-2" style={{ borderColor: '#ffe0b2' }}>
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <CardTitle className="text-lg" style={{ color: '#bf360c' }}>
                              {item.data.name}
                            </CardTitle>
                            <p className="text-sm mt-2 font-semibold" style={{ color: '#e65100' }}>
                              Reason: {item.discovery_reason}
                            </p>
                          </div>
                          <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto mt-2 sm:mt-0">
                            <Button
                              data-testid={`approve-obsolete-${index}`}
                              onClick={() => handleReview(item.id, 'approve')}
                              size="sm"
                              className="flex items-center gap-1"
                              style={{ background: '#4caf50', color: 'white' }}
                            >
                              <CheckCircle className="w-4 h-4" />
                              Keep (Approve)
                            </Button>
                            <Button
                              data-testid={`reject-obsolete-${index}`}
                              onClick={() => handleReview(item.id, 'reject')}
                              size="sm"
                              variant="destructive"
                              className="flex items-center gap-1"
                            >
                              <XCircle className="w-4 h-4" />
                              Deprecate (Reject)
                            </Button>
                          </div>
                        </div>
                      </CardHeader>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* --- PENDING SKILLS (Copied from old file) --- */}
          <Card className="mb-8 border-none shadow-lg" data-testid="pending-skills-section">
            <CardHeader>
              <CardTitle className="text-2xl" style={{ color: '#004d40' }}>Pending Skills</CardTitle>
              <CardDescription>New skills discovered from job market analysis</CardDescription>
            </CardHeader>
            <CardContent>
              {pendingSkills.length === 0 ? (
                <p className="text-center py-8" style={{ color: '#757575' }}>No pending skills</p>
              ) : (
                <div className="space-y-4">
                  {pendingSkills.map((item, index) => (
                    <Card key={index} className="border-2" style={{ borderColor: '#e0e0e0' }}>
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <CardTitle className="text-lg" style={{ color: '#004d40' }}>
                              {item.data.name}
                            </CardTitle>
                            <div className="flex items-center gap-2 mt-2">
                              <Badge variant="outline">{item.data.type}</Badge>
                              <Badge
                                style={{
                                  background: 'linear-gradient(135deg, #b2dfdb 0%, #80cbc4 100%)',
                                  color: '#004d40',
                                }}
                              >
                                Confidence: {(item.data.confidence * 100).toFixed(0)}%
                              </Badge>
                            </div>
                            <p className="text-sm mt-2" style={{ color: '#00695c' }}>
                              {item.data.discovery_reason}
                            </p>
                            <div className="mt-2">
                              <p className="text-xs font-semibold mb-1" style={{ color: '#00695c' }}>Aliases:</p>
                              <div className="flex flex-wrap gap-2">
                                {item.data.aliases.map((alias, idx) => (
                                  <span key={idx} className="text-xs px-2 py-1 rounded" style={{ background: '#e0f2f1', color: '#004d40' }}>
                                    {alias}
                                  </span>
                                ))}
                              </div>
                            </div>
                          </div>
                          <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto mt-2 sm:mt-0">
                            <Button
                              data-testid={`approve-skill-${index}`}
                              onClick={() => handleReview(item.id, 'approve')}
                              size="sm"
                              className="flex items-center gap-1"
                              style={{ background: '#4caf50', color: 'white' }}
                            >
                              <CheckCircle className="w-4 h-4" />
                              Approve
                            </Button>
                            <Button
                              data-testid={`reject-skill-${index}`}
                              onClick={() => handleReview(item.id, 'reject')}
                              size="sm"
                              variant="destructive"
                              className="flex items-center gap-1"
                            >
                              <XCircle className="w-4 h-4" />
                              Reject
                            </Button>
                          </div>
                        </div>
                      </CardHeader>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* --- PENDING ROLES (Copied from old file) --- */}
          <Card className="border-none shadow-lg" data-testid="pending-roles-section">
            <CardHeader>
              <CardTitle className="text-2xl" style={{ color: '#004d40' }}>Pending Job Roles</CardTitle>
              <CardDescription>New job roles discovered from job market analysis</CardDescription>
            </CardHeader>
            <CardContent>
              {pendingRoles.length === 0 ? (
                <p className="text-center py-8" style={{ color: '#757575' }}>No pending roles</p>
              ) : (
                <div className="space-y-4">
                  {pendingRoles.map((item, index) => (
                    <Card key={index} className="border-2" style={{ borderColor: '#e0e0e0' }}>
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <CardTitle className="text-lg" style={{ color: '#004d40' }}>
                              {item.data.title}
                            </CardTitle>
                            <CardDescription className="mt-2">{item.data.description}</CardDescription>
                            <div className="flex items-center gap-2 mt-3">
                              <Badge
                                style={{
                                  background: 'linear-gradient(135deg, #b2dfdb 0%, #80cbc4 100%)',
                                  color: '#004d40',
                                }}
                              >
                                ${item.data.salary_range[0].toLocaleString()} - ${item.data.salary_range[1].toLocaleString()}
                              </Badge>
                              <Badge variant="outline">
                                Confidence: {(item.data.confidence * 100).toFixed(0)}%
                              </Badge>
                            </div>
                            <p className="text-sm mt-2" style={{ color: '#00695c' }}>
                              {item.data.discovery_reason}
                            </p>
                            <div className="mt-3">
                              <p className="text-xs font-semibold mb-2" style={{ color: '#00695c' }}>Required Skills:</p>
                              <div className="flex flex-wrap gap-2">
                                {item.data.skill_weights.slice(0, 5).map((sw, idx) => (
                                  <span key={idx} className="text-xs px-2 py-1 rounded" style={{ background: '#e0f2f1', color: '#004d40' }}>
                                    {sw.skill} ({sw.weight})
                                  </span>
                                ))}
                              </div>
                            </div>
                          </div>
                          <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto mt-2 sm:mt-0">
                            <Button
                              data-testid={`approve-role-${index}`}
                              onClick={() => handleReview(item.id, 'approve')}
                              size="sm"
                              className="flex items-center gap-1"
                              style={{ background: '#4caf50', color: 'white' }}
                            >
                              <CheckCircle className="w-4 h-4" />
                              Approve
                            </Button>
                            <Button
                              data-testid={`reject-role-${index}`}
                              onClick={() => handleReview(item.id, 'reject')}
                              size="sm"
                              variant="destructive"
                              className="flex items-center gap-1"
                            >
                              <XCircle className="w-4 h-4" />
                              Reject
                            </Button>
                          </div>
                        </div>
                      </CardHeader>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;