import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Brain, Target, Trophy, Zap, Clock, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function LandingPage() {
  const navigate = useNavigate();

  const features = [
    {
      icon: Brain,
      title: "Adaptive Learning",
      description: "AI-powered questions that adjust to your skill level",
    },
    {
      icon: Target,
      title: "Focus Metrics",
      description: "Track response time, consistency, and cognitive patterns",
    },
    {
      icon: Trophy,
      title: "Gamified Progress",
      description: "Earn points, badges, and climb leaderboards",
    },
    {
      icon: Zap,
      title: "Instant Feedback",
      description: "Learn from mistakes with detailed explanations",
    },
    {
      icon: Clock,
      title: "Timed Challenges",
      description: "Build speed and accuracy under pressure",
    },
    {
      icon: TrendingUp,
      title: "Analytics",
      description: "Visualize your growth across topics and subjects",
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <motion.section
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6 }}
        className="relative overflow-hidden"
      >
        <div className="absolute inset-0 bg-gradient-to-br from-slate-50 via-white to-indigo-50 opacity-60" />
        <div className="container mx-auto px-4 py-20 md:py-32 relative z-10">
          <div className="max-w-4xl mx-auto text-center">
            <motion.h1
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2, duration: 0.6 }}
              className="text-4xl md:text-6xl font-serif tracking-tight text-primary leading-tight mb-6"
              data-testid="hero-title"
            >
              Master Through Focus
            </motion.h1>
            <motion.p
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.4, duration: 0.6 }}
              className="text-lg md:text-xl text-muted-foreground leading-relaxed mb-10 max-w-2xl mx-auto"
              data-testid="hero-description"
            >
              Quiz-based learning that measures what matters: accuracy, speed,
              and focus. Transform abstract concepts into mastery through
              adaptive practice.
            </motion.p>
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.6, duration: 0.6 }}
              className="flex flex-col sm:flex-row gap-4 justify-center"
            >
              <Button
                size="lg"
                onClick={() => navigate("/auth")}
                className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-full px-8 py-6 text-lg font-medium shadow-lg hover:scale-105 active:scale-95 transition-transform"
                data-testid="get-started-btn"
              >
                Get Started
              </Button>
              <Button
                size="lg"
                variant="outline"
                onClick={() => navigate("/auth")}
                className="border-2 border-primary/20 text-primary hover:bg-primary/5 rounded-full px-8 py-6 text-lg font-medium transition-all"
                data-testid="learn-more-btn"
              >
                Learn More
              </Button>
            </motion.div>
          </div>
        </div>
      </motion.section>

      {/* Features Grid */}
      <section className="py-20 bg-white">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-serif tracking-tight text-primary mb-4">
              Designed for Deep Learning
            </h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Every feature is crafted to enhance focus and accelerate mastery
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1, duration: 0.5 }}
                  className="bg-card rounded-xl border border-border/40 p-8 shadow-sm hover:shadow-md transition-all hover:-translate-y-1 cursor-pointer"
                  data-testid={`feature-card-${index}`}
                >
                  <div className="bg-accent/10 w-14 h-14 rounded-full flex items-center justify-center mb-4">
                    <Icon className="w-7 h-7 text-accent" strokeWidth={1.5} />
                  </div>
                  <h3 className="text-xl font-medium text-primary mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-muted-foreground leading-relaxed">
                    {feature.description}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-br from-slate-900 to-slate-800 text-white">
        <div className="container mx-auto px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="max-w-3xl mx-auto"
          >
            <h2 className="text-3xl md:text-5xl font-serif mb-6">
              Ready to Transform Your Learning?
            </h2>
            <p className="text-lg text-slate-300 mb-8">
              Join students who are building mental stamina and mastering
              complex concepts through focused practice.
            </p>
            <Button
              size="lg"
              onClick={() => navigate("/auth")}
              className="bg-white text-slate-900 hover:bg-slate-100 rounded-full px-10 py-6 text-lg font-semibold shadow-xl hover:scale-105 active:scale-95 transition-transform"
              data-testid="cta-start-btn"
            >
              Start Learning Today
            </Button>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 bg-slate-50 border-t border-border">
        <div className="container mx-auto px-4 text-center text-muted-foreground text-sm">
          <p>© 2026 Focus Learn. Built for students, by educators.</p>
        </div>
      </footer>
    </div>
  );
}