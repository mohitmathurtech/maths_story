import { useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Brain, ArrowLeft, Loader } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import api from "@/utils/api";

export default function QuizSelection({ user, onLogout }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    subject: "",
    topic: "",
    subtopic: "",
    difficulty: "medium",
    num_questions: 5,
  });

  const handleGenerate = async (e) => {
    e.preventDefault();
    
    if (!formData.subject || !formData.topic) {
      toast.error("Please fill in subject and topic");
      return;
    }

    setLoading(true);
    try {
      const response = await api.post("/quiz/generate", formData);
      const quiz = response.data;
      
      // Store quiz for the interface
      sessionStorage.setItem("currentQuiz", JSON.stringify(quiz));
      
      toast.success("Quiz generated successfully!");
      navigate(`/quiz/${quiz.id}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to generate quiz");
    } finally {
      setLoading(false);
    }
  };

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
          <div className="text-center mb-10">
            <h1 className="text-4xl md:text-5xl font-serif text-primary mb-4" data-testid="quiz-selection-title">
              Create Your Quiz
            </h1>
            <p className="text-lg text-muted-foreground">
              AI will generate personalized questions based on your preferences
            </p>
          </div>

          <div className="bg-card rounded-2xl border border-border shadow-lg p-8">
            <form onSubmit={handleGenerate} className="space-y-6" data-testid="quiz-form">
              <div className="space-y-2">
                <Label htmlFor="subject" className="text-base font-medium">
                  Subject *
                </Label>
                <Input
                  id="subject"
                  placeholder="e.g., Mathematics, Physics, Computer Science"
                  value={formData.subject}
                  onChange={(e) =>
                    setFormData({ ...formData, subject: e.target.value })
                  }
                  className="h-12 rounded-lg border-2"
                  required
                  data-testid="subject-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="topic" className="text-base font-medium">
                  Topic *
                </Label>
                <Input
                  id="topic"
                  placeholder="e.g., Linear Algebra, Quantum Mechanics"
                  value={formData.topic}
                  onChange={(e) =>
                    setFormData({ ...formData, topic: e.target.value })
                  }
                  className="h-12 rounded-lg border-2"
                  required
                  data-testid="topic-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="subtopic" className="text-base font-medium">
                  Subtopic (Optional)
                </Label>
                <Input
                  id="subtopic"
                  placeholder="e.g., Eigenvalues, Wave Functions"
                  value={formData.subtopic}
                  onChange={(e) =>
                    setFormData({ ...formData, subtopic: e.target.value })
                  }
                  className="h-12 rounded-lg border-2"
                  data-testid="subtopic-input"
                />
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="difficulty" className="text-base font-medium">
                    Difficulty
                  </Label>
                  <select
                    id="difficulty"
                    value={formData.difficulty}
                    onChange={(e) =>
                      setFormData({ ...formData, difficulty: e.target.value })
                    }
                    className="w-full h-12 rounded-lg border-2 border-input bg-background px-4 text-base focus:outline-none focus:ring-2 focus:ring-ring focus:border-primary"
                    data-testid="difficulty-select"
                  >
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="num_questions" className="text-base font-medium">
                    Questions
                  </Label>
                  <select
                    id="num_questions"
                    value={formData.num_questions}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        num_questions: parseInt(e.target.value),
                      })
                    }
                    className="w-full h-12 rounded-lg border-2 border-input bg-background px-4 text-base focus:outline-none focus:ring-2 focus:ring-ring focus:border-primary"
                    data-testid="num-questions-select"
                  >
                    <option value="3">3</option>
                    <option value="5">5</option>
                    <option value="10">10</option>
                    <option value="15">15</option>
                  </select>
                </div>
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-primary text-primary-foreground hover:bg-primary/90 rounded-full h-14 text-lg font-medium shadow-md hover:scale-105 active:scale-95 transition-transform"
                data-testid="generate-quiz-btn"
              >
                {loading ? (
                  <>
                    <Loader className="w-5 h-5 mr-2 animate-spin" />
                    Generating Quiz...
                  </>
                ) : (
                  "Generate Quiz"
                )}
              </Button>
            </form>
          </div>

          <div className="mt-8 bg-accent/5 rounded-xl p-6 border border-accent/20">
            <h3 className="font-semibold text-primary mb-2">How it works:</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>• AI analyzes your topic and generates relevant questions</li>
              <li>• Questions adapt to your selected difficulty level</li>
              <li>• Your response time and focus patterns are tracked</li>
              <li>• Receive instant feedback and detailed explanations</li>
            </ul>
          </div>
        </motion.div>
      </div>
    </div>
  );
}