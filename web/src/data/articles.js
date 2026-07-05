// Bilingual article data — shared by the landing "Insights" cards and /articles pages.
export const articles = [
  {
    id: 'associative-vs-rag',
    kicker: '01 · Fundamentals',
    en: {
      title: 'Why associative memory beats vector RAG',
      paras: [
        'Vector RAG matches on surface similarity: no shared keywords, no hit. It cannot connect "I dislike Python" to a later "what should I write this script in?" — the words don\'t overlap.',
        'Holographic memory smears each fact across a 10,000-dimensional space and reconstructs the signal by majority vote inside the activation radius. It survives noise and vague cues, and surfaces the connection RAG never sees: "Go — you dislike Python."',
      ],
    },
    ru: {
      title: 'Почему ассоциативная память сильнее векторного RAG',
      paras: [
        'Векторный RAG ищет по поверхностному сходству: нет общих слов — нет результата. Он не свяжет «не люблю Python» с более поздним «на чём написать скрипт?» — слова не пересекаются.',
        'Голографическая память «размазывает» факт по 10 000-мерному пространству и восстанавливает сигнал по правилу большинства внутри радиуса активации. Она устойчива к шуму и смутным запросам и находит связь, которую RAG не видит: «Go — ты же не любишь Python».',
      ],
    },
  },
  {
    id: 'sdm-equals-attention',
    kicker: '02 · Theory',
    en: {
      title: 'Sparse Distributed Memory ≈ Attention',
      paras: [
        "The engine is Kanerva's SDM, first described at MIT. Recent work (2021–2026) proved it is mathematically equivalent to the Attention mechanism inside Transformers — the very thing that powers GPT-4 and Claude.",
        'So this isn\'t exotica bolted onto an LLM. It\'s the same principle, exposed as durable, write-once-recall-forever memory the model can reach through MCP.',
      ],
    },
    ru: {
      title: 'Разреженная распределённая память ≈ Attention',
      paras: [
        'В основе — SDM Канервы, впервые описанная в MIT. Недавние работы (2021–2026) доказали её математическую эквивалентность механизму Attention в трансформерах — тому самому, на котором работают GPT-4 и Claude.',
        'Это не экзотика сбоку от LLM, а тот же принцип — только вынесенный в долговременную память, к которой модель обращается через MCP.',
      ],
    },
  },
  {
    id: 'robot-muscle-memory',
    kicker: '03 · Frontier',
    en: {
      title: 'From AI memory to a robot\'s "muscle memory"',
      paras: [
        'Kanerva designed SDM as a digital model of the cerebellum — the seat of motor skill. For narrow, motor tasks (walking, skating) that turns a weakness into a strength: repetition builds a stable interference pattern. The more it walks, the better it walks.',
        'The far horizon: bake a trained skill into a physical optical hologram and read it at the speed of light — a "crystal of parkour" for humanoid robots and drones. Today: simulation. But the vector is set.',
      ],
    },
    ru: {
      title: 'От памяти ИИ к «мышечной памяти» робота',
      paras: [
        'Канерва задумывал SDM как цифровую модель мозжечка — центра моторики. Для узких моторных задач (ходьба, катание) это превращает минус в плюс: повторение формирует устойчивую интерференционную картину. Чем больше ходишь — тем лучше ходишь.',
        'Дальний горизонт: записать навык в физическую оптическую голограмму и считывать его со скоростью света — «кристалл паркура» для человекоподобных роботов и дронов. Пока — симуляция. Но вектор задан.',
      ],
    },
  },
];
