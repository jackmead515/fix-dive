import cv2
import os

def get_playlist(base_url):
    return f"""#EXTM3U
#EXT-X-VERSION:6
#EXT-X-TARGETDURATION:6
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-PLAYLIST-TYPE:VOD
#EXT-X-INDEPENDENT-SEGMENTS
#EXTINF:5.750000,
{base_url}video_0.ts
#EXTINF:4.250000,
{base_url}video_1.ts
#EXTINF:5.750000,
{base_url}video_0.ts
#EXTINF:4.250000,
{base_url}video_1.ts
#EXT-X-ENDLIST
"""



if __name__ == "__main__":
    
    base_url = "http://172.23.0.100:30140/fix-dive-storage/projects/1234567890/playlists/Y2h1bmsubXA0MTUxZGI3ODQ2NjJjOTU3ZGY1NDMwNDY5YWRkMmU4NTE=/"
    
    playlist = get_playlist(base_url)
    
    with open('playlist.m3u8', 'w') as f:
        f.write(playlist)
    
    os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'protocol_whitelist;file,rtp,udp,crypto,data,http,https,tcp,tls'
    
    capture = cv2.VideoCapture('playlist.m3u8')
    
    while True:
        
        success, frame = capture.read()
        
        if not success:
            break
        
        cv2.imshow('frame', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    capture.release() 