import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Brain, ArrowLeft, User, Mail, Trophy, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Profile({ user, onLogout }) {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-white">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate("/dashboard")}
                className="rounded-full"
                data-testid="back-btn"
              >
                <ArrowLeft className="w-5 h-5" />
              </Button>
              <Brain className="w-8 h-8 text-accent" />
              <span className="text-xl font-serif text-primary">Focus Learn</span>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-2xl mx-auto"
        >
          <h1 className="text-4xl md:text-5xl font-serif text-primary mb-10" data-testid="profile-title">
            Profile
          </h1>

          <div className="bg-white rounded-2xl border border-border shadow-lg p-8 mb-6">
            <div className="flex items-center gap-6 mb-8">
              <div className="w-20 h-20 rounded-full bg-accent/10 flex items-center justify-center">
                <User className="w-10 h-10 text-accent" />
              </div>
              <div>
                <h2 className="text-2xl font-serif text-primary" data-testid="user-name">{user?.name}</h2>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Mail className="w-4 h-4" />
                  <span data-testid="user-email">{user?.email}</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6 pt-6 border-t border-border">
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-muted-foreground text-sm">
                  <Trophy className="w-4 h-4" />
                  <span>Level</span>
                </div>
                <div className="text-3xl font-serif text-primary" data-testid="user-level">
                  {user?.level || 1}
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-muted-foreground text-sm">
                  <Zap className="w-4 h-4" />
                  <span>Total Points</span>
                </div>
                <div className="text-3xl font-serif text-accent" data-testid="user-points">
                  {user?.points || 0}
                </div>
              </div>
            </div>
          </div>

          <Button
            onClick={onLogout}
            variant="outline"
            className="w-full border-2 border-destructive/20 text-destructive hover:bg-destructive/5 rounded-full h-12 font-medium"
            data-testid="logout-btn"
          >
            Sign Out
          </Button>
        </motion.div>
      </div>
    </div>
  );
}