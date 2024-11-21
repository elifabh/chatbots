# src/analyze_feedback.py

import pandas as pd

def analyze_feedback(log_file='feedback.log'):
    try:
        # Tab ile ayrılmış veriyi oku
        df = pd.read_csv(log_file, sep='\t', header=None, names=['Question', 'Response', 'Feedback'])
        
        # Genel geri bildirim sayısı
        total_feedback = len(df)
        
        # Beğeni ve beğenmeme sayıları
        likes = len(df[df['Feedback'] == 'like'])
        dislikes = len(df[df['Feedback'] == 'dislike'])
        
        # Oranlar
        like_ratio = (likes / total_feedback) * 100 if total_feedback > 0 else 0
        dislike_ratio = (dislikes / total_feedback) * 100 if total_feedback > 0 else 0
        
        print(f"Toplam Geri Bildirim: {total_feedback}")
        print(f"Beğeni: {likes} ({like_ratio:.2f}%)")
        print(f"Beğenmeme: {dislikes} ({dislike_ratio:.2f}%)")
        
        # En çok beğenilen sorular
        top_liked = df[df['Feedback'] == 'like']['Question'].value_counts().head(5)
        print("\nEn Çok Beğenilen Sorular:")
        print(top_liked)
        
        # En çok beğenilmeyen sorular
        top_disliked = df[df['Feedback'] == 'dislike']['Question'].value_counts().head(5)
        print("\nEn Çok Beğenilmeyen Sorular:")
        print(top_disliked)
        
    except FileNotFoundError:
        print(f"{log_file} dosyası bulunamadı.")
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    analyze_feedback()

