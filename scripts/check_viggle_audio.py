#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Viggle音轨检查工具
验证Viggle处理后的视频是否保留原音轨
"""

import subprocess
import json
import os
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ViggleAudioChecker:
    def __init__(self):
        self.downloads_dir = Path("downloads")
        self.input_dir = Path("tasks_in")
        
    def check_video_audio(self, video_path: str) -> dict:
        """检查视频的音轨信息"""
        try:
            cmd = [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_streams", "-show_format", video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return {"error": "ffprobe执行失败"}
            
            data = json.loads(result.stdout)
            
            # 分析音视频流
            video_streams = []
            audio_streams = []
            
            for stream in data.get('streams', []):
                if stream['codec_type'] == 'video':
                    video_streams.append({
                        'codec': stream.get('codec_name', 'unknown'),
                        'width': stream.get('width', 0),
                        'height': stream.get('height', 0),
                        'fps': stream.get('r_frame_rate', 'unknown')
                    })
                elif stream['codec_type'] == 'audio':
                    audio_streams.append({
                        'codec': stream.get('codec_name', 'unknown'),
                        'sample_rate': stream.get('sample_rate', 'unknown'),
                        'channels': stream.get('channels', 'unknown'),
                        'bit_rate': stream.get('bit_rate', 'unknown')
                    })
            
            # 获取格式信息
            format_info = data.get('format', {})
            
            return {
                'file_path': video_path,
                'file_size_mb': round(os.path.getsize(video_path) / (1024 * 1024), 2),
                'duration': format_info.get('duration', 'unknown'),
                'bit_rate': format_info.get('bit_rate', 'unknown'),
                'video_streams': video_streams,
                'audio_streams': audio_streams,
                'has_audio': len(audio_streams) > 0,
                'audio_count': len(audio_streams),
                'video_count': len(video_streams)
            }
            
        except Exception as e:
            return {"error": f"检查失败: {str(e)}"}
    
    def compare_audio_before_after(self, original_path: str, viggle_output_path: str) -> dict:
        """比较处理前后的音轨"""
        logger.info(f"🔍 比较音轨: {Path(original_path).name} vs {Path(viggle_output_path).name}")
        
        original_info = self.check_video_audio(original_path)
        viggle_info = self.check_video_audio(viggle_output_path)
        
        if "error" in original_info or "error" in viggle_info:
            return {
                "error": f"检查失败: 原始={original_info.get('error', 'OK')}, Viggle={viggle_info.get('error', 'OK')}"
            }
        
        # 音轨对比
        audio_comparison = {
            "original_has_audio": original_info['has_audio'],
            "viggle_has_audio": viggle_info['has_audio'],
            "audio_preserved": original_info['has_audio'] and viggle_info['has_audio'],
            "original_audio_count": original_info['audio_count'],
            "viggle_audio_count": viggle_info['audio_count']
        }
        
        # 视频质量对比
        video_comparison = {
            "original_resolution": f"{original_info['video_streams'][0]['width']}x{original_info['video_streams'][0]['height']}" if original_info['video_streams'] else "unknown",
            "viggle_resolution": f"{viggle_info['video_streams'][0]['width']}x{viggle_info['video_streams'][0]['height']}" if viggle_info['video_streams'] else "unknown",
            "original_codec": original_info['video_streams'][0]['codec'] if original_info['video_streams'] else "unknown",
            "viggle_codec": viggle_info['video_streams'][0]['codec'] if viggle_info['video_streams'] else "unknown"
        }
        
        return {
            "audio_comparison": audio_comparison,
            "video_comparison": video_comparison,
            "original_info": original_info,
            "viggle_info": viggle_info
        }
    
    def extract_audio_sample(self, video_path: str, output_dir: str = "audio_samples") -> str:
        """提取音频样本用于对比"""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        output_path = output_dir / f"{Path(video_path).stem}_audio.aac"
        
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vn", "-acodec", "copy",
            "-t", "30",  # 只提取前30秒
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"✅ 音频样本已提取: {output_path}")
            return str(output_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 音频提取失败: {e}")
            return ""
    
    def check_all_viggle_outputs(self):
        """检查所有Viggle输出文件的音轨"""
        logger.info("🔍 开始检查所有Viggle输出文件的音轨...")
        
        if not self.downloads_dir.exists():
            logger.error(f"❌ 下载目录不存在: {self.downloads_dir}")
            return
        
        viggle_files = list(self.downloads_dir.glob("*.mp4"))
        if not viggle_files:
            logger.warning("⚠️ 没有找到Viggle输出文件")
            return
        
        results = []
        for viggle_file in viggle_files:
            logger.info(f"📹 检查文件: {viggle_file.name}")
            info = self.check_video_audio(str(viggle_file))
            results.append(info)
            
            if info.get('has_audio'):
                logger.info(f"✅ {viggle_file.name} - 包含音轨 ({info['audio_count']}个)")
            else:
                logger.warning(f"⚠️ {viggle_file.name} - 缺少音轨")
        
        # 生成报告
        self.generate_audio_report(results)
        
        return results
    
    def generate_audio_report(self, results: list):
        """生成音轨检查报告"""
        report_path = Path("logs/viggle_audio_report.txt")
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("🎵 Viggle音轨检查报告\n")
            f.write("=" * 50 + "\n\n")
            
            total_files = len(results)
            files_with_audio = sum(1 for r in results if r.get('has_audio', False))
            
            f.write(f"📊 统计信息:\n")
            f.write(f"   总文件数: {total_files}\n")
            f.write(f"   包含音轨: {files_with_audio}\n")
            f.write(f"   音轨保留率: {files_with_audio/total_files*100:.1f}%\n\n")
            
            f.write("📋 详细检查结果:\n")
            f.write("-" * 30 + "\n")
            
            for result in results:
                if "error" in result:
                    f.write(f"❌ {result['file_path']}: {result['error']}\n")
                else:
                    status = "✅" if result.get('has_audio') else "⚠️"
                    f.write(f"{status} {Path(result['file_path']).name}\n")
                    f.write(f"   音轨数量: {result.get('audio_count', 0)}\n")
                    f.write(f"   文件大小: {result.get('file_size_mb', 0)}MB\n")
                    f.write(f"   时长: {result.get('duration', 'unknown')}秒\n")
                    
                    if result.get('audio_streams'):
                        audio = result['audio_streams'][0]
                        f.write(f"   音频编码: {audio.get('codec', 'unknown')}\n")
                        f.write(f"   采样率: {audio.get('sample_rate', 'unknown')}Hz\n")
                        f.write(f"   声道数: {audio.get('channels', 'unknown')}\n")
                    f.write("\n")
        
        logger.info(f"📝 音轨检查报告已生成: {report_path}")

def main():
    """主函数"""
    print("🎵 Viggle音轨检查工具")
    print("=" * 40)
    
    checker = ViggleAudioChecker()
    
    # 检查所有Viggle输出
    results = checker.check_all_viggle_outputs()
    
    if results:
        print(f"\n📊 检查完成!")
        print(f"   总文件数: {len(results)}")
        print(f"   包含音轨: {sum(1 for r in results if r.get('has_audio', False))}")
        print(f"   音轨保留率: {sum(1 for r in results if r.get('has_audio', False))/len(results)*100:.1f}%")
    
    print("\n💡 使用建议:")
    print("  1. 查看详细报告: logs/viggle_audio_report.txt")
    print("  2. 如果音轨丢失，检查Viggle处理设置")
    print("  3. 确保使用正确的会员等级")

if __name__ == "__main__":
    main()
