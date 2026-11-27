export type Lesson = {
  id: string
  title: string
  signs: readonly string[]
}

export type GesturePrediction = {
  label: string
  score: number
  margin: number
}
