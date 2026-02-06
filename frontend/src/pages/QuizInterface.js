import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate, useParams } from "react-router-dom";
import { Brain, Clock, ArrowRight, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import api from "@/utils/api";

export default function QuizInterface({ user }) {
  const { quizId } = useParams();
  const navigate = useNavigate();
  const [quiz, setQuiz] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [userAnswer, setUserAnswer] = useState("");
  const [startTime, setStartTime] = useState(Date.now());
  const [questionStartTime, setQuestionStartTime] = useState(Date.now());
  const [submitting, setSubmitting] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
    const storedQuiz = sessionStorage.getItem("currentQuiz");
    if (storedQuiz) {
      setQuiz(JSON.parse(storedQuiz));
      setQuestionStartTime(Date.now());
    } else {
      toast.error("Quiz not found");
      navigate("/quiz/select");
    }
  }, [quizId, navigate]);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, [currentIndex]);

  const handleAnswerSubmit = () => {
    if (!userAnswer.trim()) {
      toast.error("Please provide an answer");
      return;
    }

    const timeTaken = (Date.now() - questionStartTime) / 1000;
    const currentQuestion = quiz.questions[currentIndex];
    
    const answerData = {
      question_id: currentQuestion.id,
      user_answer: userAnswer,
      time_taken: timeTaken,
      is_correct: false, // Will be validated on backend
    };

    setAnswers([...answers, answerData]);
    setUserAnswer("");

    if (currentIndex < quiz.questions.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setQuestionStartTime(Date.now());
    } else {
      submitQuiz([...answers, answerData]);
    }
  };

  const submitQuiz = async (allAnswers) => {
    setSubmitting(true);
    try {
      const response = await api.post("/quiz/submit", {
        quiz_id: quizId,
        answers: allAnswers,
      });

      const result = response.data;
      sessionStorage.setItem("quizResult", JSON.stringify(result));
      sessionStorage.removeItem("currentQuiz");
      
      navigate(`/results/${result.id}`);
    } catch (error) {
      toast.error("Failed to submit quiz");
      setSubmitting(false);
    }
  };

  if (!quiz || submitting) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center" data-testid="loading-state">
        <div className="text-center">
          <div className="inline-block w-10 h-10 border-4 border-accent border-t-transparent rounded-full animate-spin mb-4"></div>
          <p className="text-muted-foreground">
            {submitting ? "Submitting your answers..." : "Loading quiz..."}
          </p>
        </div>
      </div>
    );
  }

  const currentQuestion = quiz.questions[currentIndex];
  const progress = ((currentIndex + 1) / quiz.questions.length) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50">
      {/* Progress Bar */}
      <div className="fixed top-0 left-0 w-full h-1 bg-slate-200 z-50">
        <motion.div
          className="h-full bg-accent"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.3 }}
        />
      </div>

      {/* Header */}
      <div className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Brain className="w-7 h-7 text-accent" />
            <div>
              <div className="text-sm font-semibold text-primary">
                {quiz.subject} - {quiz.topic}
              </div>
              <div className="text-xs text-muted-foreground">
                Question {currentIndex + 1} of {quiz.questions.length}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-white rounded-full px-4 py-2 border border-border shadow-sm">
            <Clock className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-mono text-primary">
              {Math.floor((Date.now() - startTime) / 1000)}s
            </span>
          </div>
        </div>
      </div>

      {/* Quiz Content */}
      <div className="container mx-auto px-4 flex items-center justify-center min-h-[calc(100vh-120px)]">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentIndex}
            initial={{ x: 50, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -50, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="w-full max-w-2xl"
          >
            <div className="bg-white rounded-2xl border border-border shadow-xl p-10" data-testid="quiz-question-card">
              {/* Question */}
              <div className="mb-10">
                <div className="text-sm uppercase tracking-widest font-semibold text-muted-foreground mb-4">
                  {currentQuestion.type === "mcq" ? "Multiple Choice" : "Alphanumeric Answer"}
                </div>
                <h2 className="text-2xl md:text-3xl font-serif text-primary leading-relaxed" data-testid="question-text">
                  {currentQuestion.question}
                </h2>
              </div>

              {/* Answer Input */}
              {currentQuestion.type === "mcq" && currentQuestion.options ? (
                <div className="space-y-3 mb-8">
                  {currentQuestion.options.map((option, idx) => (
                    <motion.button
                      key={idx}
                      whileHover={{ scale: 1.01 }}
                      whileTap={{ scale: 0.99 }}
                      onClick={() => setUserAnswer(option.charAt(0))}
                      className={`w-full text-left p-5 rounded-xl border-2 transition-all ${
                        userAnswer === option.charAt(0)
                          ? "border-accent bg-accent/5 shadow-md"
                          : "border-border hover:border-accent/50 bg-white"
                      }`}
                      data-testid={`option-${idx}`}
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                            userAnswer === option.charAt(0)
                              ? "border-accent bg-accent"
                              : "border-border"
                          }`}
                        >
                          {userAnswer === option.charAt(0) && (
                            <CheckCircle className="w-4 h-4 text-white" />
                          )}
                        </div>
                        <span className="text-base text-primary">{option}</span>
                      </div>
                    </motion.button>
                  ))}
                </div>
              ) : (
                <div className="mb-8">
                  <Input
                    ref={inputRef}
                    type="text"
                    placeholder="Type your answer here..."
                    value={userAnswer}
                    onChange={(e) => setUserAnswer(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        handleAnswerSubmit();
                      }
                    }}
                    className="text-2xl font-serif text-center border-b-2 border-primary/20 bg-transparent focus:border-primary focus:ring-0 rounded-none px-0 h-16"
                    data-testid="alphanumeric-input"
                  />
                </div>
              )}

              {/* Submit Button */}
              <Button
                onClick={handleAnswerSubmit}
                disabled={!userAnswer}
                className="w-full bg-primary text-primary-foreground hover:bg-primary/90 rounded-full h-14 text-lg font-medium shadow-md hover:scale-105 active:scale-95 transition-transform disabled:opacity-50 disabled:hover:scale-100"
                data-testid="submit-answer-btn"
              >
                {currentIndex < quiz.questions.length - 1 ? (
                  <>
                    Next Question
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </>
                ) : (
                  "Submit Quiz"
                )}
              </Button>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}