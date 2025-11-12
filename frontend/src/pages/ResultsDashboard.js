import { useLocation, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { Sparkles, ArrowLeft, CheckCircle2, XCircle, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import CareerVisualizer from "@/components/CareerVisualizer";
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

const ResultsDashboard = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [selectedJob, setSelectedJob] = useState(null);

  const { userSkills, careerMatches } = location.state || {};

  useEffect(() => {
    if (!userSkills || !careerMatches) {
      navigate("/");
    }
  }, [userSkills, careerMatches, navigate]);

  if (!userSkills || !careerMatches) {
    return null;
  }

  // Get top 3 matches for visualizer
  const top3Matches = careerMatches.slice(0, 3);

  // Donut chart component
  const DonutChart = ({ score }) => {
    const data = [
      { name: 'Match', value: score },
      { name: 'Gap', value: 100 - score },
    ];

    const COLORS = ['#00897b', '#e0e0e0'];

    return (
      <ResponsiveContainer width={120} height={120}>
        <PieChart>
          <Pie
            data={data}
            cx={60}
            cy={60}
            innerRadius={35}
            outerRadius={50}
            paddingAngle={2}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
    );
  };

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #f5f7fa 0%, #e8f5e9 100%)' }}>
      {/* Header */}
      <nav className="glass" style={{ borderBottom: '1px solid rgba(255,255,255,0.2)' }}>
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-7 h-7" style={{ color: '#00695c' }} />
            <h1 className="text-2xl font-bold" style={{ color: '#004d40' }}>NextStepAI</h1>
          </div>
          <Button
            data-testid="analyze-another-resume-button"
            variant="outline"
            onClick={() => navigate("/")}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Analyze Another Resume
          </Button>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="fade-in">
          {/* Career Path Visualizer */}
          <Card className="mb-8 border-none shadow-lg" data-testid="career-visualizer-section">
            <CardHeader>
              <CardTitle className="text-2xl" style={{ color: '#004d40' }}>Your Career Roadmap</CardTitle>
              <CardDescription>Interactive visualization of your potential career paths</CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              <CareerVisualizer matches={top3Matches} onNodeClick={setSelectedJob} />
            </CardContent>
          </Card>

          {/* Skills Profile */}
          <Card className="mb-8 border-none shadow-lg" data-testid="skills-profile-card">
            <CardHeader>
              <CardTitle className="text-2xl" style={{ color: '#004d40' }}>Your Skills Have Been Identified</CardTitle>
              <CardDescription>We found {userSkills.length} skills in your resume</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-3">
                {userSkills.map((skill, index) => (
                  <span
                    key={index}
                    data-testid={`skill-tag-${index}`}
                    className="px-4 py-2 rounded-full text-sm font-medium transition-transform hover:scale-105"
                    style={{
                      background: 'linear-gradient(135deg, #b2dfdb 0%, #80cbc4 100%)',
                      color: '#004d40',
                      boxShadow: '0 2px 8px rgba(0, 137, 123, 0.2)',
                    }}
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Career Matches */}
          <Card className="border-none shadow-lg" data-testid="career-matches-section">
            <CardHeader>
              <CardTitle className="text-2xl" style={{ color: '#004d40' }}>Your Recommended Career Paths</CardTitle>
              <CardDescription>Top {careerMatches.length} roles matched to your skills</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-6">
                {careerMatches.map((match, index) => (
                  <Card
                    key={index}
                    data-testid={`job-card-${index}`}
                    className="border-2 transition-all hover:shadow-xl"
                    style={{
                      borderColor: selectedJob === match.title ? '#00897b' : '#e0e0e0',
                      background: selectedJob === match.title ? '#e0f2f1' : 'white',
                    }}
                  >
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-xl mb-2" style={{ color: '#004d40' }}>
                            {match.title}
                          </CardTitle>
                          <CardDescription className="text-sm mb-3">
                            {match.description}
                          </CardDescription>
                          <p className="text-lg font-semibold" style={{ color: '#00695c' }}>
                            ${match.salary_range[0].toLocaleString()} - ${match.salary_range[1].toLocaleString()}
                          </p>
                        </div>
                        <div className="flex flex-col items-center">
                          <DonutChart score={match.match_score} />
                          <p className="text-2xl font-bold mt-2" style={{ color: '#00897b' }}>
                            {match.match_score}%
                          </p>
                          <p className="text-xs" style={{ color: '#00695c' }}>Match</p>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <Tabs defaultValue="matching" className="w-full">
                        <TabsList className="grid w-full grid-cols-3">
                          <TabsTrigger value="matching" data-testid={`matching-tab-${index}`}>Matching Skills</TabsTrigger>
                          <TabsTrigger value="gaps" data-testid={`gaps-tab-${index}`}>Skill Gaps</TabsTrigger>
                          <TabsTrigger value="upskill" data-testid={`upskill-tab-${index}`}>Upskilling</TabsTrigger>
                        </TabsList>

                        <TabsContent value="matching" className="mt-4">
                          <div className="space-y-2">
                            {match.matching_skills.length > 0 ? (
                              match.matching_skills.map((skill, idx) => (
                                <div key={idx} className="flex items-center justify-between p-3 rounded-lg" style={{ background: '#e8f5e9' }}>
                                  <div className="flex items-center gap-2">
                                    <CheckCircle2 className="w-5 h-5" style={{ color: '#2e7d32' }} />
                                    <span className="font-medium" style={{ color: '#1b5e20' }}>{skill.skill}</span>
                                  </div>
                                  <span className="text-sm" style={{ color: '#558b2f' }}>Weight: {skill.weight}</span>
                                </div>
                              ))
                            ) : (
                              <p className="text-center py-4" style={{ color: '#757575' }}>No matching skills found</p>
                            )}
                          </div>
                        </TabsContent>

                        <TabsContent value="gaps" className="mt-4">
                          <div className="space-y-2">
                            {match.missing_skills.length > 0 ? (
                              match.missing_skills.map((skill, idx) => (
                                <div key={idx} className="flex items-center justify-between p-3 rounded-lg" style={{ background: '#ffebee' }}>
                                  <div className="flex items-center gap-2">
                                    <XCircle className="w-5 h-5" style={{ color: '#c62828' }} />
                                    <span className="font-medium" style={{ color: '#b71c1c' }}>{skill.skill}</span>
                                  </div>
                                  <span className="text-sm" style={{ color: '#d32f2f' }}>Weight: {skill.weight}</span>
                                </div>
                              ))
                            ) : (
                              <p className="text-center py-4" style={{ color: '#2e7d32' }}>You have all required skills!</p>
                            )}
                          </div>
                        </TabsContent>

                        <TabsContent value="upskill" className="mt-4">
                          <div className="space-y-4">
                            {match.missing_skills.length > 0 ? (
                              match.missing_skills.map((skill, idx) => (
                                <Card key={idx} className="border" style={{ borderColor: '#e0e0e0' }}>
                                  <CardHeader className="pb-3">
                                    <CardTitle className="text-base" style={{ color: '#004d40' }}>{skill.skill}</CardTitle>
                                    <CardDescription className="text-xs">Importance: {(skill.weight * 100).toFixed(0)}%</CardDescription>
                                  </CardHeader>
                                  <CardContent>
                                    {skill.learning_resources && skill.learning_resources.length > 0 ? (
                                      <div className="space-y-2">
                                        {skill.learning_resources.map((resource, ridx) => (
                                          <Button
                                            key={ridx}
                                            data-testid={`learn-button-${index}-${idx}-${ridx}`}
                                            variant="outline"
                                            className="w-full justify-between"
                                            onClick={() => window.open(resource, '_blank')}
                                            style={{
                                              borderColor: '#00897b',
                                              color: '#00897b',
                                            }}
                                          >
                                            <span>Learn Now - Course {ridx + 1}</span>
                                            <ExternalLink className="w-4 h-4" />
                                          </Button>
                                        ))}
                                      </div>
                                    ) : (
                                      <p className="text-sm" style={{ color: '#757575' }}>No resources available</p>
                                    )}
                                  </CardContent>
                                </Card>
                              ))
                            ) : (
                              <p className="text-center py-4" style={{ color: '#2e7d32' }}>You have all required skills for this role!</p>
                            )}
                          </div>
                        </TabsContent>
                      </Tabs>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ResultsDashboard;
