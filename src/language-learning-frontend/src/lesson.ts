export type Lesson = {
  id: string
  title: string
  signs: readonly string[]
}

// Labels match id_to_label in model-service/storage/embeddings/train_embeddings.npz.
export const lessons: readonly Lesson[] = [
  {
    id: '1',
    title: 'Everyday signs',
    signs: ['YES', 'NO', 'SMILE', 'CALL', 'DEAF', 'VALUE'],
  },
  {
    id: '2',
    title: 'People & work',
    signs: ['MAN', 'WOMAN', 'KID', 'STUDENT', 'FIREMAN', 'MECHANIC', 'HEAD'],
  },
  {
    id: '3',
    title: 'Daily routine',
    signs: ['MORNING', 'NOON', 'NIGHT', 'BREAKFAST', 'LUNCH', 'EAT'],
  },
  {
    id: '4',
    title: 'Animals & colors',
    signs: ['DOG', 'CAT 3', 'BEE', 'FISH', 'GREEN', 'RED'],
  },
  {
    id: '5',
    title: 'Places & travel',
    signs: ['CAR', 'TRIP', 'HOSPITAL', 'UNIVERSITY'],
  },
  {
    id: '6',
    title: 'Sports & celebrations',
    signs: ['BASKETBALL', 'FOOTBALL', 'CHRISTMAS'],
  },
]
