# Silk Vocal Studio
All-in-One Python GUI for easily creating CV / CVVC / VCV voicebanks for the vocal synthesizer UTAU. Create base folder, record samples, auto generate the oto.ini and package in one go.

## About

### Features
- Simple but modern PyQT5 GUI
- Create base folder with sample folder and `character.txt` for voicebank info
- Recording from a `reclist.txt` file
- Recording visualisation with `matplotlib`
- Automatic configuration of oto.ini file
- Packaging to zip

Info: This is currently in planning phase.

### Why Silk Vocal Studio?
Silk Vocal Studio removes the annoying process of needing to install multiple applications to create a voicebank, which includes the recording software (like OREMO or Recstar) and the oto.ini generator (setParam or MoreSampler) or editor (UTAU oto editor, vLabeler).
Silk Vocal Studio combines the main parts of making a UTAU voicebank and even makes it easy to package a voicebank to the final product.

<details>
<summary>
Explanation "UTAU"
</summary>

Info: This is for those who are not familiar with UTAU itself. This repository does not include UTAU, this part is just information.

### What is UTAU?
UTAU is a vocal synthesizer which released as a freemium alternative to the popular VOCALOID software by Yamaha in 2008. In the software, you select a voicebank, draw your notes into the piano roll, and assign lyrics to it. UTAU lets you easily preview the notes in a project.

### What is a voicebank?
A voicebank is basically "the singer" that you have to select in UTAU to make it sing. A Voicebank consists out of two main components:
- Samples Folder: This folder includes the different audio recordings of the syllables needed to make it sing a full language, for example japanese.
- oto.ini: This is a configuration file which includes variables for every recording. UTAU needs this file to correctly render a syllable in the software. For example, let's say we have the japanese syllable か (ka) and record it with recording software. Without an oto.ini, UTAU will not know where syllable starts, the consonant ends and when the vowel starts, when it can be looped (which is the part where the waveform of the "a" vowel looks stable) and when it ends, which will not render the syllable in UTAU.
</details>
