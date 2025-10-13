import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { RefreshCw, ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { mockQuestions, generateMockEvaluation } from "@/lib/mockData";
import { useToast } from "@/hooks/use-toast";

const Practice = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [essay, setEssay] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const currentQuestion = mockQuestions[currentQuestionIndex];

  const handleNewQuestion = () => {
    setCurrentQuestionIndex((prev) => (prev + 1) % mockQuestions.length);
    setEssay("");
    toast({
      title: "New question generated",
      description: "Start writing your essay below",
    });
  };

  const handleSubmit = () => {
    if (essay.trim().length < 50) {
      toast({
        title: "Essay too short",
        description: "Please write at least 50 words",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);
    
    // Simulate API call
    setTimeout(() => {
      const evaluation = generateMockEvaluation(currentQuestion.id, essay);
      setIsSubmitting(false);
      
      // Store evaluation in sessionStorage for the results page
      sessionStorage.setItem("latestEvaluation", JSON.stringify(evaluation));
      sessionStorage.setItem("evaluationQuestion", JSON.stringify(currentQuestion));
      
      navigate("/evaluation");
    }, 2000);
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
            <Button onClick={handleNewQuestion} variant="outline">
              <RefreshCw className="mr-2 h-4 w-4" />
              New Question
            </Button>
          </div>

          <Card>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="mb-2">Task 2 Question</CardTitle>
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
                </div>
              </div>
              <CardDescription className="text-base leading-relaxed">
                {currentQuestion.question}
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
                  disabled={isSubmitting || wordCount < 50}
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
