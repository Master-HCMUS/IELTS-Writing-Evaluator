// Types for the IELTS Writing Evaluator

export interface EssayQuestion {
  id: string;
  question: string;
  topic: string;
  difficulty: 'easy' | 'medium' | 'hard';
}

// API Response Types
export interface EvaluationError {
  span: string;
  type: string;
  fix: string;
}

export interface EvaluationSuggestion {
  suggestion: string;
}

export interface EvaluationCriterion {
  name: string;
  band: number;
  evidence_quotes: string[];
  errors: EvaluationError[];
  suggestions: string[];
}

export interface EvaluationMeta {
  prompt_hash: string;
  model: string;
  schema_version: string;
  rubric_version: string;
  token_usage: {
    input_tokens: number;
    output_tokens: number;
  };
}

export interface EvaluationResult {
  per_criterion: EvaluationCriterion[];
  overall: number;
  votes: number[];
  dispersion: number;
  confidence: string;
  meta: EvaluationMeta;
}

export interface EssayEvaluation {
  id: string;
  questionId: string;
  essay: string;
  overallScore: number;
  taskResponse: number;
  coherenceCohesion: number;
  lexicalResource: number;
  grammaticalRange: number;
  strengths: string[];
  weaknesses: string[];
  feedback: {
    taskResponse: string;
    coherenceCohesion: string;
    lexicalResource: string;
    grammaticalRange: string;
  };
  submittedAt: Date;
}

export interface CourseRecommendation {
  targetBand: number;
  currentBand: number;
  duration: number; // in months
  weeklyPlan: {
    week: number;
    objectives: string[];
    exercises: string[];
  }[];
  focusAreas: {
    area: string;
    priority: 'high' | 'medium' | 'low';
    exercises: string[];
  }[];
}

export const mockQuestions: EssayQuestion[] = [
  {
    id: '1',
    question: 'Some people believe that technology has made our lives more complex. Others think it has made life easier. Discuss both views and give your own opinion.',
    topic: 'Technology',
    difficulty: 'medium'
  },
  {
    id: '2',
    question: 'Many people believe that social networking sites have a negative impact on individuals and society. To what extent do you agree or disagree?',
    topic: 'Social Media',
    difficulty: 'medium'
  },
  {
    id: '3',
    question: 'Some people think that universities should provide graduates with the knowledge and skills needed in the workplace. Others think that the true function of a university should be to give access to knowledge for its own sake. Discuss both views and give your own opinion.',
    topic: 'Education',
    difficulty: 'hard'
  },
  {
    id: '4',
    question: 'In many countries, the proportion of older people is steadily increasing. Does this trend have more positive or negative effects on society?',
    topic: 'Society',
    difficulty: 'medium'
  },
  {
    id: '5',
    question: 'Some people believe that children should be allowed to stay at home and play until they are six or seven years old. Others believe that it is important for young children to go to school as soon as possible. Discuss both views and give your own opinion.',
    topic: 'Education',
    difficulty: 'easy'
  }
];

export const generateMockEvaluation = (questionId: string, essay: string): EssayEvaluation => {
  // Generate realistic but random scores
  const taskResponse = Math.random() * 2 + 5; // 5-7
  const coherenceCohesion = Math.random() * 2 + 5.5; // 5.5-7.5
  const lexicalResource = Math.random() * 2 + 5; // 5-7
  const grammaticalRange = Math.random() * 2 + 5.5; // 5.5-7.5
  const overallScore = (taskResponse + coherenceCohesion + lexicalResource + grammaticalRange) / 4;

  return {
    id: Date.now().toString(),
    questionId,
    essay,
    overallScore: Math.round(overallScore * 2) / 2, // Round to nearest 0.5
    taskResponse: Math.round(taskResponse * 2) / 2,
    coherenceCohesion: Math.round(coherenceCohesion * 2) / 2,
    lexicalResource: Math.round(lexicalResource * 2) / 2,
    grammaticalRange: Math.round(grammaticalRange * 2) / 2,
    strengths: [
      'Good use of topic-specific vocabulary',
      'Clear paragraph structure',
      'Appropriate use of examples',
    ],
    weaknesses: [
      'Some grammatical errors affecting clarity',
      'Limited range of complex sentence structures',
      'Could develop ideas more fully',
    ],
    feedback: {
      taskResponse: 'You have addressed all parts of the task and presented a clear position. However, some ideas could be developed more fully with additional supporting details.',
      coherenceCohesion: 'Your essay has a clear structure with good paragraphing. Consider using more cohesive devices to improve the flow between ideas.',
      lexicalResource: 'You demonstrate a good range of vocabulary with some less common items. Be careful with word choice accuracy in places.',
      grammaticalRange: 'You use a mix of simple and complex sentence structures. Focus on reducing grammatical errors and using more sophisticated structures accurately.',
    },
    submittedAt: new Date(),
  };
};

export const generateMockCourseRecommendation = (
  currentBand: number,
  targetBand: number,
  duration: number
): CourseRecommendation => {
  const weeklyPlan = [];
  const totalWeeks = duration * 4;

  for (let week = 1; week <= totalWeeks; week++) {
    if (week <= totalWeeks / 3) {
      weeklyPlan.push({
        week,
        objectives: [
          'Master essay structure and organization',
          'Build foundation vocabulary',
          'Practice basic grammar patterns',
        ],
        exercises: [
          'Write 2 practice essays',
          'Learn 50 new academic words',
          'Complete grammar exercises',
        ],
      });
    } else if (week <= (totalWeeks * 2) / 3) {
      weeklyPlan.push({
        week,
        objectives: [
          'Develop complex sentence structures',
          'Enhance coherence and cohesion',
          'Expand lexical range',
        ],
        exercises: [
          'Write 3 practice essays',
          'Study cohesive devices',
          'Practice paraphrasing',
        ],
      });
    } else {
      weeklyPlan.push({
        week,
        objectives: [
          'Perfect task achievement',
          'Refine advanced grammar',
          'Build exam confidence',
        ],
        exercises: [
          'Complete 4 timed essays',
          'Review and analyze model answers',
          'Take practice tests',
        ],
      });
    }
  }

  return {
    targetBand,
    currentBand,
    duration,
    weeklyPlan,
    focusAreas: [
      {
        area: 'Grammatical Range and Accuracy',
        priority: 'high',
        exercises: [
          'Practice complex sentences daily',
          'Review common error patterns',
          'Complete grammar drills',
        ],
      },
      {
        area: 'Lexical Resource',
        priority: 'medium',
        exercises: [
          'Learn topic-specific vocabulary',
          'Practice collocations',
          'Study academic word list',
        ],
      },
      {
        area: 'Task Response',
        priority: 'high',
        exercises: [
          'Analyze question types',
          'Practice planning essays',
          'Study band 8-9 responses',
        ],
      },
      {
        area: 'Coherence and Cohesion',
        priority: 'medium',
        exercises: [
          'Master linking words',
          'Practice paragraph development',
          'Study text organization',
        ],
      },
    ],
  };
};
