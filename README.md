# Ameno: HackGen ベースの Nerd Fonts 更新版

この Fork は Nerd Fonts **3.5.1** を使用し、OpenAI (`U+EC81`) と Claude (`U+EC82`) のアイコンを追加します。通常文字の形状・文字幅を維持するため、同一環境で更新前後をビルドして比較します。

通常の Unicode に割り当てられた電源記号・ハート・稲妻などは既存の形状を保持し、私用領域の Nerd アイコンを更新します。

配布フォントは原版の予約名を避けて **Ameno** とします。HackGen Console NF に対応するフォント名は **Ameno Console NF** です。

## ビルドと検証

GitHub Actions の **Build and verify fonts** を実行してください。成功した run の `Ameno-NerdFonts-3.5.1-...` artifact に 12 本の TTF、ライセンス、比較結果、素材の SHA-256 とビルド環境を収録します。artifact の保存期間は 30 日です。

検証では通常文字の輪郭・advance・LSB・ヒンティングとフォントの主要メトリクスを比較し、NF 版 4 本に両アイコンが収録されていることを確認します。改名後にも全グリフを再比較します。実際の端末での見え方は、インストール後に確認してください。

Nerd Fonts 素材の出典とチェックサムは `source/NERD_FONTS_VERSION.json` にあります。更新時は公式リリースの `Hack.zip` の SHA-256 を検証し、Regular/Bold 素材と `hackgen_generator.sh` の収録範囲を更新してください。CI の baseline は更新前コミットに固定しています。

以下は原版の説明です。

---

# プログラミングフォント 白源 (はくげん／HackGen)

HackGen is a composite font of Hack and GenJyuu-Gothic.

白源 (はくげん／HackGen) は、プログラミング向け英文フォント Hack と、源ノ角ゴシックの派生フォント源柔ゴシックを合成したプログラミングフォントです。  

![image](https://github.com/yuru7/HackGen/assets/13458509/ea0c0dae-58ea-4712-8ed2-570274b87039)

2つのフォントをただ合成しただけではなく、一部の独自改変により更なる視認性向上を図っています。

* 文字幅 半角1:全角2 の正統派な等幅フォント (文字幅 半角3:全角5 バージョンも同梱)
* Hack 由来の読みやすく、しっとりとした印象の英字
* 源柔ゴシック由来の引き締まりつつ、丸ゴシックの風合いのあるカナ文字・漢字 (第一～第四水準漢字まで対応)
* 全角スペースの可視化、パイプ記号 `|` の破断線化 (Ricty Discord インスパイア)
* 英字部分にはヒンティングを付与することで明瞭な表示
* Powerline 記号の表示
* その他、判読性の向上
  * 濁点、半濁点を通常より大きくし、表示サイズが小さい場合でも区別しやすくした
  * 長音記号 `ー` と漢数字の1 `一` にアクセントを付け区別しやすくした
  * カタカナ `ヘ` にアクセントを付け、ひらがなと区別しやすくした

> 💡 その他、公開中のプログラミングフォント
> - 日本語文字に IBM Plex Sans JP、英数字部分に IBM Plex Mono を使った [**PlemolJP (プレモル ジェイピー)**](https://github.com/yuru7/PlemolJP)
> - 日本語文字にBIZ UDゴシック、英数字部分に JetBrains Mono を使った [**UDEV Gothic**](https://github.com/yuru7/udev-gothic)
> - 日本語文字に源真ゴシック、英数字部分に Fira Mono を使った [**Firge (ファージ)**](https://github.com/yuru7/Firge)

|**白源 通常版**|**白源 半角3:全角5 版**|
|:------------------------:|:------------------------:|
|![hackgen](https://user-images.githubusercontent.com/13458509/133928601-cb1d3e00-6c4b-4ce5-a945-44ae2baa81e0.png)|![hackgen35](https://user-images.githubusercontent.com/13458509/133928624-77ed3d0b-8e6c-46c1-89e1-3e85f6d0c215.png)|

## フォントファミリーの種類

**※いずれのフォントにも Powerline 記号が含まれています。**

|**フォント ファミリー**|**説明**|
|:------------:|:---|
|**HackGen**|文字幅比率「半角1:全角2」の通常版の白源。主にASCIIコードの英数字記号に Hack ベースの字体を使い、その他の記号類やかな文字・漢字を源柔ゴシックベースにしている|
|**HackGen Console**|Hack ベースの字体を除外せずに全て適用したフォントファミリー。矢印記号などの多くの記号が半角で表示されるため、コンソールでの利用や記号類は可能な限り半角で表示したい人にオススメ|
|**HackGen35**|通常版の白源の文字幅比率を「半角3:全角5」にしたフォントファミリー。英数字が通常版の白源よりも大きく表示される。日本語が少ない文書やコードの場合にはこちらの方が読みやすいと感じるかもしれない|
|**HackGen35 Console**|HackGen Console  の文字幅比率を 半角3:全角5 にしたフォントファミリー|

|**HackGen 系統**|**HackGen35 系統**|
|:---:|:---:|
|`HackGen`<br/>![hackgen](https://github.com/yuru7/HackGen/raw/image/hikaku_hackgen.png)|`HackGen35`<br/>![hackgen35](https://github.com/yuru7/HackGen/raw/image/hikaku_hackgen35.png)|
|`HackGen Console`<br/>![hackgen console](https://github.com/yuru7/HackGen/raw/image/hikaku_hackgen-console.png)|`HackGen35 Console`<br/>![hackgen35 console](https://github.com/yuru7/HackGen/raw/image/hikaku_hackgen35-console.png)|

また、追加で提供している `HackGen NF` `HackGen35 NF` フォントファミリーには、[Nerd Fonts](https://www.nerdfonts.com/) を追加合成しており、Font Awesome をはじめとした多くのアイコンフォントが表示できるようになります。  

## フォントのインストール

ビルド済みの ttf ファイルは GitHub のリリースページからダウンロードできます。  
ダウンロードした ttf ファイルは、各 OS に応じた手順でインストールしてください。

[Release - HackGen](https://github.com/yuru7/HackGen/releases/latest)

* `HackGen_バージョン.zip` は従来の HackGen/HackGen35
* `HackGen_NF_バージョン.zip` は従来の HackGen/HackGen35 に [Nerd Fonts](https://www.nerdfonts.com/) を追加合成したもの

### Homebrew によるフォントのインストール

Mac の Homebrew ユーザーは以下のコマンドでもインストールすることができます。  
※Homebrew リポジトリに追加してくださったのはユーザーさんなので、使用方法などをリポジトリオーナーはサポートできません。悪しからずご了承ください。

```
$ brew install font-hackgen
$ brew install font-hackgen-nerd
```

### Chocolatey によるフォントのインストール

Windows の [Chocolatey](https://chocolatey.org/) ユーザーは以下のコマンドでもインストールすることができます。  
[font-hackgen](https://chocolatey.org/packages/font-hackgen) が Nerd Fonts を含まないフォント、[font-hackgen-nerd](https://chocolatey.org/packages/font-hackgen-nerd) が Nerd Fonts を含むフォントです。  
※インストールに失敗する場合は、[パッケージのリポジトリ](https://github.com/kai2nenobu/chocolatey-packages/)にissueを投稿してください。

```
> choco install font-hackgen
> choco install font-hackgen-nerd
```

## ビルド環境

HackGen は以下の環境でビルドしています。

* OS: Ubuntu 20.04.2 (Kubuntu)
* Tools
  * ttfautohint: 1.8.3
  * fonttools: 3.44.0
  * fontforge: 20201107

### ビルドツールのインストール方法と注意点

* ttfautohint: `sudo apt install ttfautohint`
* fonttools: Python 2 の pip で `sudo pip2 install fonttools`
  * fonttools に含まれるサブツール `pyftmerge` と `ttx` をコマンドとして利用しているため、`sudo` を使ってシステム全体で使えるようにする
  * Python 3 の pip を使ったものは fonttools 4.13.0 がインストールされる (2020/08/01 時点)。 fonttools 4.13.0 では post テーブルの構造が変わってしまうため、macOS 10.15 にてインストール不可となる ([#12](https://github.com/yuru7/HackGen/issues/12))
* fontforge: [公式サイト](https://fontforge.org/en-US/downloads/) よりダウンロード
