import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ArrowLeft, TrendingUp, CheckCircle2, AlertCircle } from "lucide-react";
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";
import type { EssayEvaluation, EssayQuestion } from "@/lib/mockData";

const Evaluation = () => {
  const navigate = useNavigate();
  const [evaluation, setEvaluation] = useState<EssayEvaluation | null>(null);
  const [question, setQuestion] = useState<EssayQuestion | null>(null);

  useEffect(() => {
    const storedEvaluation = sessionStorage.getItem("latestEvaluation");
    const storedQuestion = sessionStorage.getItem("evaluationQuestion");
    
    if (storedEvaluation) {
      setEvaluation(JSON.parse(storedEvaluation));
    }
    
    if (storedQuestion) {
      setQuestion(JSON.parse(storedQuestion));
    }
    
    if (!storedEvaluation) {
      navigate("/practice");
    }
  }, [navigate]);

  if (!evaluation || !question) {
    return null;
  }

  const radarData = [
    { subject: "Task Response", score: evaluation.taskResponse, fullMark: 9 },
    { subject: "Coherence & Cohesion", score: evaluation.coherenceCohesion, fullMark: 9 },
    { subject: "Lexical Resource", score: evaluation.lexicalResource, fullMark: 9 },
    { subject: "Grammatical Range", score: evaluation.grammaticalRange, fullMark: 9 },
  ];

  const barData = [
    { name: "Task Response", score: evaluation.taskResponse },
    { name: "Coherence & Cohesion", score: evaluation.coherenceCohesion },
    { name: "Lexical Resource", score: evaluation.lexicalResource },
    { name: "Grammatical Range", score: evaluation.grammaticalRange },
  ];

  const getScoreColor = (score: number) => {
    if (score >= 7) return "text-success";
    if (score >= 6) return "text-warning";
    return "text-destructive";
  };

  const getBandDescription = (score: number) => {
    if (score >= 8) return "Excellent";
    if (score >= 7) return "Good";
    if (score >= 6) return "Competent";
    if (score >= 5) return "Modest";
    return "Needs Improvement";
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container flex h-16 items-center justify-between">
          <Button variant="ghost" onClick={() => navigate("/practice")}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Practice
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => navigate("/course")}>
              Get Study Plan
            </Button>
            <Button onClick={() => navigate("/dashboard")}>Dashboard</Button>
          </div>
        </div>
      </header>

      <main className="container py-8">
        <div className="mx-auto max-w-6xl space-y-6">
          <div className="text-center">
            <h1 className="mb-2 text-4xl font-bold">Your Evaluation Results</h1>
            <p className="text-muted-foreground">Detailed analysis of your IELTS Writing Task 2 essay</p>
          </div>

          {/* Overall Score */}
          <Card className="border-2 border-primary/20 bg-gradient-to-br from-primary/5 to-secondary/5">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl">Overall Band Score</CardTitle>
              <div className={`text-6xl font-bold ${getScoreColor(evaluation.overallScore)}`}>
                {evaluation.overallScore}
              </div>
              <CardDescription className="text-lg">{getBandDescription(evaluation.overallScore)}</CardDescription>
            </CardHeader>
          </Card>

          {/* Score Breakdown */}
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Score Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={radarData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="subject" />
                    <PolarRadiusAxis angle={90} domain={[0, 9]} />
                    <Radar name="Your Score" dataKey="score" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={0.6} />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Individual Scores</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={barData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" angle={-15} textAnchor="end" height={100} />
                    <YAxis domain={[0, 9]} />
                    <Tooltip />
                    <Bar dataKey="score" fill="hsl(var(--chart-2))" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Detailed Scores */}
          <div className="grid gap-6 md:grid-cols-2">
            {[
              { title: "Task Response", score: evaluation.taskResponse, feedback: evaluation.feedback.taskResponse },
              { title: "Coherence & Cohesion", score: evaluation.coherenceCohesion, feedback: evaluation.feedback.coherenceCohesion },
              { title: "Lexical Resource", score: evaluation.lexicalResource, feedback: evaluation.feedback.lexicalResource },
              { title: "Grammatical Range", score: evaluation.grammaticalRange, feedback: evaluation.feedback.grammaticalRange },
            ].map((item) => (
              <Card key={item.title}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>{item.title}</CardTitle>
                    <Badge className={getScoreColor(item.score)} variant="outline">
                      {item.score}/9
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">{item.feedback}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Strengths and Weaknesses */}
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-success" />
                  Strengths
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {evaluation.strengths.map((strength, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="text-success">•</span>
                      <span className="text-sm">{strength}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-warning" />
                  Areas for Improvement
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {evaluation.weaknesses.map((weakness, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="text-warning">•</span>
                      <span className="text-sm">{weakness}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>

          {/* Next Steps */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Next Steps
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="mb-4 text-sm text-muted-foreground">
                Ready to improve your score? Get a personalized study plan tailored to your current level and target band.
              </p>
              <Button onClick={() => navigate("/course")}>Create My Study Plan</Button>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default Evaluation;
