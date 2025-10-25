import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { RefreshCw, ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { apiClient, GenerateQuestionResponse, ScoreRequest } from "@/lib/api";
import { EssayEvaluation } from "@/lib/mockData";
import { useToast } from "@/hooks/use-toast";

const Practice = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [currentQuestion, setCurrentQuestion] = useState<GenerateQuestionResponse | null>(null);
  const [essay, setEssay] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isGeneratingQuestion, setIsGeneratingQuestion] = useState(false);

  // Generate initial question on component mount
  useEffect(() => {
    generateNewQuestion();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const generateNewQuestion = async () => {
    setIsGeneratingQuestion(true);
    try {
      const question = await apiClient.generateQuestion({ difficulty: 'medium' });
      setCurrentQuestion(question);
      setEssay("");
      toast({
        title: "New question generated",
        description: "Start writing your essay below",
      });
    } catch (error) {
      console.error('Failed to generate question:', error);
      toast({
        title: "Error generating question",
        description: "Please try again",
        variant: "destructive",
      });
    } finally {
      setIsGeneratingQuestion(false);
    }
  };

  const handleNewQuestion = () => {
    generateNewQuestion();
  };

  const handleSubmit = async () => {
    const trimmedEssay = essay.trim();
    const words = trimmedEssay.split(/\s+/).filter(Boolean);
    
    if (words.length < 250) {
      toast({
        title: "Essay too short",
        description: "Task 2 essay must be at least 250 words",
        variant: "destructive",
      });
      return;
    }

    if (!currentQuestion) {
      toast({
        title: "No question available",
        description: "Please generate a question first",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const scoreRequest: ScoreRequest = {
        task_type: 'task2',
        essay: essay.trim(),
        question: currentQuestion.question,
      };

      const evaluation = await apiClient.scoreEssay(scoreRequest);

      // Validate evaluation data
      if (!evaluation || 
          !Array.isArray(evaluation.per_criterion) ||
          !evaluation.per_criterion.every(c => 
            typeof c.band === 'number' && 
            typeof c.name === 'string' &&
            Array.isArray(c.evidence_quotes) &&
            Array.isArray(c.errors) &&
            Array.isArray(c.suggestions)
          ) ||
          typeof evaluation.overall !== 'number' ||
          !Array.isArray(evaluation.votes) ||
          typeof evaluation.dispersion !== 'number' ||
          typeof evaluation.confidence !== 'string' ||
          !evaluation.meta) {
        console.error('Invalid evaluation structure:', evaluation);
        throw new Error("Invalid evaluation data received from API");
      }

      // Store the evaluation result and question for the evaluation page
      sessionStorage.setItem("latestEvaluation", JSON.stringify(evaluation));
      sessionStorage.setItem("evaluationQuestion", JSON.stringify(currentQuestion));
      sessionStorage.setItem("evaluationQuestion", JSON.stringify(currentQuestion));

      navigate("/evaluation");
    } catch (error) {
      console.error('Failed to evaluate essay:', error);
      let errorMessage = "Please try again";
      
      if (error instanceof Error) {
        if (error.message === "Invalid evaluation data received from API") {
          errorMessage = "The evaluation service returned invalid data. Our team has been notified.";
        } else if (error.message.includes("Network") || error.message.includes("timeout")) {
          errorMessage = "Network error. Please check your connection and try again.";
        } else if (error.message.includes("500")) {
          errorMessage = "The evaluation service is temporarily unavailable. Please try again later.";
        }
      }
      
      toast({
        title: "Evaluation failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const wordCount = essay.trim().split(/\s+/).filter(Boolean).length;

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container flex h-16 items-center justify-between">
          <Button variant="ghost" onClick={() => navigate("/")}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Home
          </Button>
          <Button variant="outline" onClick={() => navigate("/dashboard")}>
            Dashboard
          </Button>
        </div>
      </header>

      <main className="container py-8">
        <div className="mx-auto max-w-4xl space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold">IELTS Writing Practice</h1>
            <Button onClick={handleNewQuestion} variant="outline" disabled={isGeneratingQuestion}>
              <RefreshCw className={`mr-2 h-4 w-4 ${isGeneratingQuestion ? 'animate-spin' : ''}`} />
              {isGeneratingQuestion ? 'Generating...' : 'New Question'}
            </Button>
          </div>

          <Card>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="mb-2">Task 2 Question</CardTitle>
                  {currentQuestion ? (
                    <div className="mb-4 flex gap-2">
                      <Badge variant="secondary">{currentQuestion.topic}</Badge>
                      <Badge variant={
                        currentQuestion.difficulty === 'easy' ? 'default' :
                          currentQuestion.difficulty === 'medium' ? 'secondary' :
                            'outline'
                      }>
                        {currentQuestion.difficulty}
                      </Badge>
                    </div>
                  ) : (
                    <div className="mb-4 flex gap-2">
                      <Badge variant="secondary">Loading...</Badge>
                    </div>
                  )}
                </div>
              </div>
              <CardDescription className="text-base leading-relaxed">
                {currentQuestion ? currentQuestion.question : "Generating question..."}
              </CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Your Essay</CardTitle>
              <CardDescription>
                Write your response below. Aim for at least 250 words.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="Start writing your essay here..."
                value={essay}
                onChange={(e) => setEssay(e.target.value)}
                className="min-h-[400px] font-mono"
              />
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  Word count: <span className={wordCount < 250 ? "text-warning" : "text-success"}>{wordCount}</span>
                  {wordCount < 250 && " (minimum 250 words)"}
                </p>
                <Button
                  onClick={handleSubmit}
                  disabled={isSubmitting || wordCount < 50 || !currentQuestion}
                  size="lg"
                >
                  {isSubmitting ? "Evaluating..." : "Submit for Evaluation"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default Practice;
