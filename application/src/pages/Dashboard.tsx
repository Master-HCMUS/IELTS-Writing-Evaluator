import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, FileText, TrendingUp, Target, Calendar } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

const Dashboard = () => {
  const navigate = useNavigate();

  // Mock progress data
  const progressData = [
    { date: "Week 1", overall: 5.5, tr: 5.5, cc: 6.0, lr: 5.0, gra: 5.5 },
    { date: "Week 2", overall: 5.75, tr: 6.0, cc: 6.0, lr: 5.5, gra: 5.5 },
    { date: "Week 3", overall: 6.0, tr: 6.0, cc: 6.5, lr: 5.5, gra: 6.0 },
    { date: "Week 4", overall: 6.25, tr: 6.5, cc: 6.5, lr: 6.0, gra: 6.0 },
    { date: "Week 5", overall: 6.5, tr: 6.5, cc: 7.0, lr: 6.0, gra: 6.5 },
  ];

  const recentEssays = [
    { id: 1, topic: "Technology", score: 6.5, date: "2025-10-08", status: "completed" },
    { id: 2, topic: "Education", score: 6.0, date: "2025-10-05", status: "completed" },
    { id: 3, topic: "Environment", score: 6.25, date: "2025-10-01", status: "completed" },
  ];

  const stats = [
    { label: "Essays Completed", value: "12", icon: FileText, color: "text-primary" },
    { label: "Current Band", value: "6.5", icon: TrendingUp, color: "text-success" },
    { label: "Target Band", value: "7.5", icon: Target, color: "text-secondary" },
    { label: "Days Practicing", value: "35", icon: Calendar, color: "text-warning" },
  ];

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container flex h-16 items-center justify-between">
          <Button variant="ghost" onClick={() => navigate("/")}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Home
          </Button>
          <Button onClick={() => navigate("/practice")}>New Practice</Button>
        </div>
      </header>

      <main className="container py-8">
        <div className="mx-auto max-w-7xl space-y-6">
          <div>
            <h1 className="mb-2 text-3xl font-bold">Your Dashboard</h1>
            <p className="text-muted-foreground">Track your progress and performance over time</p>
          </div>

          {/* Stats Cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {stats.map((stat) => (
              <Card key={stat.label}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">{stat.label}</CardTitle>
                  <stat.icon className={`h-4 w-4 ${stat.color}`} />
                </CardHeader>
                <CardContent>
                  <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Progress Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Score Progress Over Time</CardTitle>
              <CardDescription>Your improvement across all criteria</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={350}>
                <LineChart data={progressData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis domain={[4, 9]} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="overall" stroke="hsl(var(--chart-1))" strokeWidth={3} name="Overall" />
                  <Line type="monotone" dataKey="tr" stroke="hsl(var(--chart-2))" name="Task Response" />
                  <Line type="monotone" dataKey="cc" stroke="hsl(var(--chart-3))" name="Coherence & Cohesion" />
                  <Line type="monotone" dataKey="lr" stroke="hsl(var(--chart-4))" name="Lexical Resource" />
                  <Line type="monotone" dataKey="gra" stroke="hsl(var(--chart-5))" name="Grammar" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid gap-6 md:grid-cols-2">
            {/* Recent Essays */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Essays</CardTitle>
                <CardDescription>Your latest practice submissions</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentEssays.map((essay) => (
                    <div key={essay.id} className="flex items-center justify-between rounded-lg border p-4">
                      <div>
                        <p className="font-medium">{essay.topic}</p>
                        <p className="text-sm text-muted-foreground">{essay.date}</p>
                      </div>
                      <div className="text-right">
                        <Badge variant="secondary">Band {essay.score}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
                <Button variant="outline" className="mt-4 w-full" onClick={() => navigate("/practice")}>
                  View All Essays
                </Button>
              </CardContent>
            </Card>

            {/* Recommendations */}
            <Card>
              <CardHeader>
                <CardTitle>Recommendations</CardTitle>
                <CardDescription>Personalized tips to improve</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="rounded-lg border bg-muted/50 p-4">
                    <h3 className="mb-2 font-semibold">Focus on Grammar</h3>
                    <p className="text-sm text-muted-foreground">
                      Your grammar scores are slightly lower. Practice complex sentence structures daily.
                    </p>
                  </div>
                  <div className="rounded-lg border bg-muted/50 p-4">
                    <h3 className="mb-2 font-semibold">Expand Vocabulary</h3>
                    <p className="text-sm text-muted-foreground">
                      Learn 10 new academic words per day to boost your Lexical Resource score.
                    </p>
                  </div>
                  <div className="rounded-lg border bg-muted/50 p-4">
                    <h3 className="mb-2 font-semibold">Practice Regularly</h3>
                    <p className="text-sm text-muted-foreground">
                      You're on track! Keep practicing 3-4 essays per week to maintain progress.
                    </p>
                  </div>
                </div>
                <Button className="mt-4 w-full" onClick={() => navigate("/course")}>
                  Get Personalized Plan
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
