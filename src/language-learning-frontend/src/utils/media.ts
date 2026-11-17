/**
 * Parses any media URL into embeddable iframe or direct video / image formats.
 * Supports YouTube (watch, share, shorts, embed), Vimeo, and direct media files.
 */
export function parseMediaUrl(url: string): {
  isYouTube: boolean
  isVimeo: boolean
  embedUrl?: string
  isDirectVideo: boolean
  isImage: boolean
} {
  const cleanUrl = url.trim()
  if (!cleanUrl) {
    return { isYouTube: false, isVimeo: false, isDirectVideo: false, isImage: false }
  }

  // YouTube match: watch?v=ID, youtu.be/ID, embed/ID, shorts/ID
  const ytMatch = cleanUrl.match(
    /(?:youtu\.be\/|youtube\.com\/(?:watch\?(?:.*&)?v=|embed\/|shorts\/|v\/))([\w-]{11})/,
  )
  if (ytMatch && ytMatch[1]) {
    const videoId = ytMatch[1]
    return {
      isYouTube: true,
      isVimeo: false,
      embedUrl: `https://www.youtube.com/embed/${videoId}?autoplay=1&mute=1&loop=1&playlist=${videoId}&controls=1`,
      isDirectVideo: true,
      isImage: false,
    }
  }

  // Vimeo match
  const vimeoMatch = cleanUrl.match(/vimeo\.com\/(?:video\/)?(\d+)/)
  if (vimeoMatch && vimeoMatch[1]) {
    const vimeoId = vimeoMatch[1]
    return {
      isYouTube: false,
      isVimeo: true,
      embedUrl: `https://player.vimeo.com/video/${vimeoId}?autoplay=1&muted=1&loop=1`,
      isDirectVideo: true,
      isImage: false,
    }
  }

  const isImageExt = /\.(png|jpe?g|gif|webp|svg|bmp)(\?.*)?$/i.test(cleanUrl)
  const isVideoExt = /\.(mp4|webm|ogg|mov|m4v)(\?.*)?$/i.test(cleanUrl)

  return {
    isYouTube: false,
    isVimeo: false,
    isDirectVideo: isVideoExt,
    isImage: isImageExt,
  }
}
