import { useEffect, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ArrowLeft, TrendingUp, CheckCircle2, AlertCircle } from "lucide-react";
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";
import type { EvaluationResult, EssayQuestion } from "@/lib/mockData";

const Evaluation = () => {
  const navigate = useNavigate();
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);
  const [question, setQuestion] = useState<EssayQuestion | null>(null);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const storedEvaluation = sessionStorage.getItem("latestEvaluation");
    const storedQuestion = sessionStorage.getItem("evaluationQuestion");
    
    console.log("Raw stored evaluation:", storedEvaluation);
    console.log("Raw stored question:", storedQuestion);
    
    if (!storedEvaluation || !storedQuestion) {
      setError("No evaluation data found. Please submit your essay first.");
      setTimeout(() => navigate("/practice"), 3000);
      return;
    }
    
    try {
      const parsedEvaluation = JSON.parse(storedEvaluation);
      const parsedQuestion = JSON.parse(storedQuestion);
      
      console.log("Parsed evaluation:", parsedEvaluation);
      console.log("Parsed question:", parsedQuestion);
      
      if (!parsedEvaluation?.overall || !parsedEvaluation?.per_criterion) {
        throw new Error("Invalid evaluation data structure");
      }
      
      setEvaluation(parsedEvaluation);
      setQuestion(parsedQuestion);
    } catch (error) {
      console.error("Error processing data:", error);
      setError("There was an error processing your evaluation. Please try again.");
      setTimeout(() => navigate("/practice"), 3000);
    }
  }, [navigate]);

  // Data calculations using useMemo to avoid premature evaluation
  const { radarData, barData, getCriterionScore, getCriterionData, formattedData } = useMemo(() => {
    console.log("useMemo evaluation:", evaluation); // Debug log

    const defaultReturn = {
      radarData: [],
      barData: [],
      getCriterionScore: () => 0,
      getCriterionData: () => null,
      formattedData: {
        overall: "0.0",
        dispersion: "0.0",
        votes: [],
        confidence: "",
      },
    };

    if (!evaluation?.per_criterion || !evaluation?.overall) {
      console.log("Returning default values due to missing data"); // Debug log
      return defaultReturn;
    }

    const getCriterionScoreFn = (name: string): number => {
      const criterion = evaluation.per_criterion.find(c => c.name === name);
      return criterion?.band || 0;
    };

    const getCriterionDataFn = (name: string) => {
      return evaluation.per_criterion.find(c => c.name === name);
    };

    // Debug log
    console.log("Formatting values:", {
      overall: evaluation.overall,
      dispersion: evaluation.dispersion,
      votes: evaluation.votes,
    });

    const formatted = {
      overall: Number(evaluation.overall).toFixed(1),
      dispersion: Number(evaluation.dispersion || 0).toFixed(1),
      votes: (evaluation.votes || []).map(v => Number(v).toFixed(1)),
      confidence: evaluation.confidence || "",
    };

    // Debug log before creating chart data
    console.log("Criterion scores:", {
      taskResponse: getCriterionScoreFn("Task Response"),
      coherence: getCriterionScoreFn("Coherence & Cohesion"),
      lexical: getCriterionScoreFn("Lexical Resource"),
      grammar: getCriterionScoreFn("Grammatical Range & Accuracy")
    });

    const radarDataArray = evaluation.per_criterion.map(criterion => ({
      subject: criterion.name,
      score: criterion.band,
      fullMark: 9
    }));

    const barDataArray = evaluation.per_criterion.map(criterion => ({
      name: criterion.name,
      score: criterion.band
    }));

    return {
      radarData: radarDataArray,
      barData: barDataArray,
      getCriterionScore: getCriterionScoreFn,
      getCriterionData: getCriterionDataFn,
      formattedData: formatted,
    };
  }, [evaluation]);

  if (!evaluation || !question) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          {error ? (
            <>
              <h2 className="text-2xl font-bold mb-4 text-destructive">{error}</h2>
              <p className="text-muted-foreground">Redirecting you back to practice...</p>
            </>
          ) : (
            <>
              <h2 className="text-2xl font-bold mb-4">Loading your evaluation...</h2>
              <p className="text-muted-foreground">Please wait while we process your results</p>
            </>
          )}
        </div>
      </div>
    );
  }

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
              <div className={`text-6xl font-bold ${getScoreColor(Number(formattedData.overall))}`}>
                {formattedData.overall}
              </div>
              <CardDescription className="text-lg">
                {getBandDescription(Number(formattedData.overall))}
                {Number(formattedData.dispersion) > 0 && (
                  <span className="block text-sm text-muted-foreground mt-1">
                    Score variation: ±{formattedData.dispersion} bands
                  </span>
                )}
                {formattedData.confidence === "high" && (
                  <span className="block text-sm text-success mt-1">
                    High confidence score
                  </span>
                )}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex justify-center gap-4">
                {formattedData.votes.map((vote, index) => (
                  <div key={index} className="text-center">
                    <div className="text-sm text-muted-foreground">Evaluator {index + 1}</div>
                    <div className={`font-medium ${getScoreColor(Number(vote))}`}>{vote}</div>
                  </div>
                ))}
              </div>
            </CardContent>
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
            {(evaluation?.per_criterion || []).map((criterion) => {
              const evidence = criterion?.evidence_quotes || [];
              const errors = criterion?.errors || [];
              const suggestions = criterion?.suggestions || [];
              const band = criterion?.band || 0;
              
              return (
                <Card key={criterion?.name}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle>{criterion?.name}</CardTitle>
                      <Badge className={getScoreColor(band)} variant="outline">
                        {band.toFixed(1)}/9
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Evidence Quotes */}
                    {evidence.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium mb-2">Evidence:</h4>
                        <ul className="space-y-1">
                          {evidence.map((quote, index) => (
                            <li key={index} className="text-sm text-muted-foreground italic">
                              "{quote}"
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Errors */}
                    {errors.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium mb-2 text-warning">Issues:</h4>
                        <ul className="space-y-2">
                          {errors.map((error, index) => (
                            <li key={index} className="text-sm">
                              <span className="font-medium">"{error?.span}"</span>
                              <br />
                              <span className="text-muted-foreground">{error?.fix}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Suggestions */}
                    {suggestions.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium mb-2 text-success">Suggestions:</h4>
                        <ul className="space-y-1">
                          {suggestions.map((suggestion, index) => (
                            <li key={index} className="text-sm text-muted-foreground">
                              • {suggestion}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Strengths and Areas for Improvement */}
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
                  {(evaluation?.per_criterion || [])
                    .filter(criterion => (criterion?.band || 0) >= 6.5)
                    .map((criterion, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <span className="text-success">•</span>
                        <span className="text-sm">
                          Strong {criterion?.name?.toLowerCase()} (Band {(criterion?.band || 0).toFixed(1)})
                        </span>
                      </li>
                    ))}
                  {formattedData.confidence === "high" && (
                    <li className="flex items-start gap-2">
                      <span className="text-success">•</span>
                      <span className="text-sm">High confidence in evaluation results</span>
                    </li>
                  )}
                  {(evaluation?.per_criterion || [])
                    .filter(criterion => (criterion?.errors || []).length === 0)
                    .map((criterion, index) => (
                      <li key={`no-errors-${index}`} className="flex items-start gap-2">
                        <span className="text-success">•</span>
                        <span className="text-sm">
                          No major errors in {criterion?.name?.toLowerCase()}
                        </span>
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
                  {(evaluation?.per_criterion || [])
                    .filter(criterion => (criterion?.band || 0) < 6.0)
                    .map((criterion, index) => (
                      <li key={`low-band-${index}`} className="flex items-start gap-2">
                        <span className="text-warning">•</span>
                        <span className="text-sm">
                          {criterion?.name} needs significant improvement (Band {(criterion?.band || 0).toFixed(1)})
                        </span>
                      </li>
                    ))}
                  {(evaluation?.per_criterion || [])
                    .filter(criterion => (criterion?.suggestions || []).length > 0)
                    .map((criterion, index) => (
                      <li key={`suggestions-${index}`} className="flex items-start gap-2">
                        <span className="text-warning">•</span>
                        <div className="text-sm">
                          <div>{criterion?.name}:</div>
                          <ul className="ml-4 mt-1 space-y-1">
                            {(criterion?.suggestions || []).map((suggestion, sIndex) => (
                              <li key={sIndex} className="list-disc">
                                {suggestion}
                              </li>
                            ))}
                          </ul>
                        </div>
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
