import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BookOpen, TrendingUp, Target, Clock } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { AuthModal, UserMenu } from "@/components/auth";
import { useAuth } from "@/contexts/AuthContext";
import heroImage from "@/assets/hero-image.jpg";
import aiFeedbackImage from "@/assets/ai-feedback.jpg";
import improveImage from "@/assets/improve.jpg";
import progressTrackingImage from "@/assets/progress-tracking.jpg";

const Landing = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { user } = useAuth();
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

  const features = [
    {
      icon: BookOpen,
      title: t('landing.features.aiEvaluation'),
      description: t('landing.features.aiEvaluationDesc'),
    },
    {
      icon: TrendingUp,
      title: t('landing.features.practiceTests'),
      description: t('landing.features.practiceTestsDesc'),
    },
    {
      icon: Target,
      title: t('landing.features.progressTracking'),
      description: t('landing.features.progressTrackingDesc'),
    },
    {
      icon: Clock,
      title: t('landing.features.trackProgress'),
      description: t('landing.features.trackProgressDesc'),
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border/50 bg-background/80 backdrop-blur-sm">
        <div className="container flex h-14 items-center justify-between">
          <div className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-primary" />
            <span className="text-lg font-medium">{t('landing.title')}</span>
          </div>
          <div className="flex items-center gap-2">
            <LanguageSwitcher />
            {user ? (
              <>
                <Button variant="outline" size="sm" onClick={() => navigate("/dashboard")}>
                  {t('dashboard.title')}
                </Button>
                <UserMenu />
              </>
            ) : (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setAuthMode('login');
                    setAuthModalOpen(true);
                  }}
                >
                  {t('auth.login.button')}
                </Button>
                <Button
                  size="sm"
                  onClick={() => {
                    setAuthMode('register');
                    setAuthModalOpen(true);
                  }}
                >
                  {t('auth.register.button')}
                </Button>
              </>
            )}
          </div>
        </div>
      </header>

      <main>
        {/* Hero Section */}
        <section className="relative overflow-hidden border-b border-border/50">
          <div className="container py-16 md:py-20">
            <div className="grid gap-8 lg:grid-cols-2 lg:gap-12 items-center">
              <div className="space-y-6">
                <h1 className="text-3xl font-medium tracking-tight sm:text-4xl md:text-5xl">
                  {t('landing.title')} with{" "}
                  <span className="text-primary">{t('landing.subtitle')}</span>
                </h1>
                <p className="text-base text-muted-foreground leading-relaxed">
                  {t('landing.description')}
                </p>
                <div className="flex flex-col gap-3 sm:flex-row">
                  <Button
                    size="lg"
                    onClick={() => {
                      if (user) {
                        navigate("/practice");
                      } else {
                        setAuthMode('login');
                        setAuthModalOpen(true);
                      }
                    }}
                  >
                    {t('practice.startPractice')}
                  </Button>
                  <Button
                    size="lg"
                    variant="outline"
                    onClick={() => {
                      if (user) {
                        navigate("/dashboard");
                      } else {
                        setAuthMode('register');
                        setAuthModalOpen(true);
                      }
                    }}
                  >
                    {t('dashboard.title')}
                  </Button>
                </div>
              </div>
              <div className="relative lg:h-[400px]">
                <img
                  src={heroImage}
                  alt="IELTS Writing Analytics Dashboard"
                  className="rounded-lg border border-border/50 shadow-2xl w-full h-full object-cover"
                />
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="container py-16 md:py-20">
          <div className="mb-12 text-center space-y-3">
            <h2 className="text-2xl font-medium">{t('landing.features.title')}</h2>
            <p className="text-sm text-muted-foreground">{t('landing.subtitle')}</p>
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            {features.map((feature) => (
              <Card key={feature.title} className="border-border/50 transition-all hover:border-primary/30">
                <CardHeader className="space-y-3">
                  <feature.icon className="h-8 w-8 text-primary" />
                  <CardTitle className="text-lg font-medium">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-sm leading-relaxed">{feature.description}</CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* How It Works */}
        <section className="border-t border-border/50 bg-muted/20">
          <div className="container py-16 md:py-20">
            <div className="mb-12 text-center space-y-3">
              <h2 className="text-2xl font-medium">How It Works</h2>
              <p className="text-sm text-muted-foreground">Three simple steps to improve your writing</p>
            </div>
            <div className="mx-auto max-w-5xl">
              <div className="grid gap-8 md:grid-cols-3">
                {[
                  { step: 1, title: "Get a Question", description: "Choose from AI-generated IELTS Task 2 questions", image: aiFeedbackImage },
                  { step: 2, title: "Write Your Essay", description: "Submit your essay for instant evaluation", image: progressTrackingImage },
                  { step: 3, title: "Learn & Improve", description: "Review feedback and follow your personalized study plan", image: improveImage },
                ].map((item) => (
                  <div key={item.step} className="space-y-4">
                    <div className="relative aspect-square rounded-lg border border-border/50 overflow-hidden">
                      <img src={item.image} alt={item.title} className="w-full h-full object-cover" />
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full border border-primary/50 bg-primary/10 text-sm font-medium text-primary">
                          {item.step}
                        </div>
                        <h3 className="text-base font-medium">{item.title}</h3>
                      </div>
                      <p className="text-sm text-muted-foreground leading-relaxed">{item.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="container py-16 md:py-20">
          <Card className="border-border/50 bg-card/50">
            <CardHeader className="text-center space-y-3">
              <CardTitle className="text-2xl font-medium">Ready to Achieve Your Target Score?</CardTitle>
              <CardDescription className="text-sm">
                Join thousands of students improving their IELTS writing skills with AI-powered feedback
              </CardDescription>
            </CardHeader>
            <CardContent className="flex justify-center pt-2">
              <Button
                size="lg"
                onClick={() => {
                  if (user) {
                    navigate("/practice");
                  } else {
                    setAuthMode('register');
                    setAuthModalOpen(true);
                  }
                }}
              >
                Start Your First Practice
              </Button>
            </CardContent>
          </Card>
        </section>
      </main>

      <footer className="border-t border-border/50 py-6">
        <div className="container text-center text-xs text-muted-foreground">
          <p>© 2025 ScoreSculpt AI. All rights reserved.</p>
        </div>
      </footer>

      <AuthModal
        open={authModalOpen}
        onOpenChange={setAuthModalOpen}
        defaultMode={authMode}
      />
    </div>
  );
};

export default Landing;
