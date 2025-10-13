import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Calendar, Target, TrendingUp } from "lucide-react";
import { generateMockCourseRecommendation } from "@/lib/mockData";
import type { CourseRecommendation } from "@/lib/mockData";

const Course = () => {
  const navigate = useNavigate();
  const [currentBand, setCurrentBand] = useState([6.0]);
  const [targetBand, setTargetBand] = useState([7.0]);
  const [duration, setDuration] = useState([3]);
  const [recommendation, setRecommendation] = useState<CourseRecommendation | null>(null);

  const handleGeneratePlan = () => {
    const plan = generateMockCourseRecommendation(currentBand[0], targetBand[0], duration[0]);
    setRecommendation(plan);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'destructive';
      case 'medium':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container flex h-16 items-center justify-between">
          <Button variant="ghost" onClick={() => navigate("/evaluation")}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Results
          </Button>
          <Button variant="outline" onClick={() => navigate("/dashboard")}>
            Dashboard
          </Button>
        </div>
      </header>

      <main className="container py-8">
        <div className="mx-auto max-w-5xl space-y-6">
          <div className="text-center">
            <h1 className="mb-2 text-3xl font-bold">Personalized Study Plan</h1>
            <p className="text-muted-foreground">Get a tailored learning path to reach your target band</p>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Configure Your Goals</CardTitle>
              <CardDescription>Set your current level, target score, and preferred study duration</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label>Current Band Score: {currentBand[0].toFixed(1)}</Label>
                <Slider
                  value={currentBand}
                  onValueChange={setCurrentBand}
                  min={4}
                  max={8}
                  step={0.5}
                  className="w-full"
                />
              </div>

              <div className="space-y-2">
                <Label>Target Band Score: {targetBand[0].toFixed(1)}</Label>
                <Slider
                  value={targetBand}
                  onValueChange={setTargetBand}
                  min={5}
                  max={9}
                  step={0.5}
                  className="w-full"
                />
              </div>

              <div className="space-y-2">
                <Label>Study Duration: {duration[0]} month{duration[0] > 1 ? 's' : ''}</Label>
                <Slider
                  value={duration}
                  onValueChange={setDuration}
                  min={1}
                  max={12}
                  step={1}
                  className="w-full"
                />
              </div>

              <Button onClick={handleGeneratePlan} className="w-full" size="lg">
                Generate My Study Plan
              </Button>
            </CardContent>
          </Card>

          {recommendation && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Your Learning Journey</CardTitle>
                  <CardDescription>
                    From Band {recommendation.currentBand} to Band {recommendation.targetBand} in {recommendation.duration} months
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-4 text-center">
                    <div className="flex-1 rounded-lg border bg-muted/50 p-4">
                      <Target className="mx-auto mb-2 h-8 w-8 text-primary" />
                      <p className="text-2xl font-bold">{recommendation.targetBand}</p>
                      <p className="text-sm text-muted-foreground">Target Band</p>
                    </div>
                    <div className="flex-1 rounded-lg border bg-muted/50 p-4">
                      <Calendar className="mx-auto mb-2 h-8 w-8 text-secondary" />
                      <p className="text-2xl font-bold">{recommendation.duration * 4}</p>
                      <p className="text-sm text-muted-foreground">Weeks</p>
                    </div>
                    <div className="flex-1 rounded-lg border bg-muted/50 p-4">
                      <TrendingUp className="mx-auto mb-2 h-8 w-8 text-success" />
                      <p className="text-2xl font-bold">+{(recommendation.targetBand - recommendation.currentBand).toFixed(1)}</p>
                      <p className="text-sm text-muted-foreground">Band Increase</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Focus Areas</CardTitle>
                  <CardDescription>Priority areas based on your current performance</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {recommendation.focusAreas.map((area) => (
                    <div key={area.area} className="rounded-lg border p-4">
                      <div className="mb-3 flex items-start justify-between">
                        <h3 className="font-semibold">{area.area}</h3>
                        <Badge variant={getPriorityColor(area.priority)}>
                          {area.priority} priority
                        </Badge>
                      </div>
                      <ul className="space-y-1">
                        {area.exercises.map((exercise, idx) => (
                          <li key={idx} className="text-sm text-muted-foreground">
                            • {exercise}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Weekly Study Plan</CardTitle>
                  <CardDescription>Detailed breakdown of your learning journey</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {recommendation.weeklyPlan.slice(0, 8).map((week) => (
                      <div key={week.week} className="rounded-lg border p-4">
                        <h3 className="mb-2 font-semibold">Week {week.week}</h3>
                        <div className="space-y-2">
                          <div>
                            <p className="mb-1 text-sm font-medium">Objectives:</p>
                            <ul className="space-y-1 pl-4">
                              {week.objectives.map((obj, idx) => (
                                <li key={idx} className="text-sm text-muted-foreground">• {obj}</li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <p className="mb-1 text-sm font-medium">Exercises:</p>
                            <ul className="space-y-1 pl-4">
                              {week.exercises.map((ex, idx) => (
                                <li key={idx} className="text-sm text-muted-foreground">• {ex}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </div>
                    ))}
                    {recommendation.weeklyPlan.length > 8 && (
                      <p className="text-center text-sm text-muted-foreground">
                        And {recommendation.weeklyPlan.length - 8} more weeks...
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>

              <div className="flex gap-4">
                <Button onClick={() => navigate("/practice")} className="flex-1">
                  Start Practicing
                </Button>
                <Button onClick={() => navigate("/dashboard")} variant="outline" className="flex-1">
                  View Dashboard
                </Button>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
};

export default Course;
