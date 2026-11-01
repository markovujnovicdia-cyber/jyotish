#!/usr/bin/env python3
"""Static OpenStep/project wiring checks. This does not compile iOS code."""
from pathlib import Path
import json
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'Jyotish.xcodeproj'


def parse_openstep(text):
    tokens = re.findall(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|[{}()=;,]|[^\s{}()=;,]+', text, re.S)
    tokens = [t for t in tokens if not t.startswith(('//', '/*'))]
    position = 0

    def take(expected=None):
        nonlocal position
        if position >= len(tokens):
            raise ValueError('Unexpected end of project')
        value = tokens[position]
        position += 1
        if expected is not None and value != expected:
            raise ValueError(f'Expected {expected!r}, found {value!r}')
        return value

    def parse():
        token = take()
        if token == '{':
            result = {}
            while tokens[position] != '}':
                key = take()
                if key.startswith('"'):
                    key = json.loads(key)
                if key in result:
                    raise ValueError(f'Duplicate dictionary key {key}')
                take('=')
                result[key] = parse()
                take(';')
            take('}')
            return result
        if token == '(':
            result = []
            while tokens[position] != ')':
                result.append(parse())
                if tokens[position] != ')':
                    take(',')
            take(')')
            return result
        return json.loads(token) if token.startswith('"') else token

    result = parse()
    if position != len(tokens):
        raise ValueError('Unexpected tokens after project root')
    return result


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate():
    project = parse_openstep((PROJECT / 'project.pbxproj').read_text())
    objects = project['objects']
    require(project['rootObject'] in objects, 'Missing project root')

    def walk(value):
        if isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif re.fullmatch('[A-F0-9]{24}', value):
            require(value in objects, f'Dangling project reference {value}')

    walk(project)
    root = objects[project['rootObject']]
    targets = {objects[tid]['name']: tid for tid in root['targets']}
    require(set(targets) == {'Jyotish', 'JyotishTests', 'JyotishUITests'}, 'Unexpected target membership')
    packages = [objects[pid] for pid in root.get('packageReferences', [])]
    require(any(p.get('relativePath') == 'Packages/JyotishCore' for p in packages), 'Local core package missing')
    require((ROOT / 'Packages/JyotishCore/Package.swift').is_file(), 'Core package manifest missing')

    seen_paths = set()

    def group_files(group_id, directory):
        group = objects[group_id]
        directory = directory / group.get('path', '')
        for child_id in group.get('children', []):
            child = objects[child_id]
            if child['isa'] == 'PBXGroup':
                group_files(child_id, directory)
            elif child['isa'] == 'PBXFileReference' and child.get('sourceTree') == '<group>':
                path = directory / child['path']
                require(path.exists(), f'Missing project file {path.relative_to(ROOT)}')
                seen_paths.add(path.resolve())

    group_files(root['mainGroup'], ROOT)
    for source in (ROOT / 'iPhoneSwiftUI').glob('*.swift'):
        require(source.resolve() in seen_paths, f'Swift file omitted from project: {source.name}')
    for name, target_id in targets.items():
        target = objects[target_id]
        phases = [objects[pid] for pid in target['buildPhases']]
        sources = [p for p in phases if p['isa'] == 'PBXSourcesBuildPhase']
        require(len(sources) == 1 and sources[0]['files'], f'{name}: source build phase missing')
        require(len(sources[0]['files']) == len(set(sources[0]['files'])), f'{name}: duplicate sources')
        if name != 'JyotishUITests':
            dependencies = [objects[did]['productName'] for did in target.get('packageProductDependencies', [])]
            require('JyotishCore' in dependencies, f'{name}: core product not linked')
        configs = objects[target['buildConfigurationList']]['buildConfigurations']
        for config_id in configs:
            settings = objects[config_id]['buildSettings']
            require(settings['IPHONEOS_DEPLOYMENT_TARGET'] == '17.0', f'{name}: unexpected deployment target')
            require(not any('NSAllowsLocalNetworking' in k or 'NSLocalNetworkUsageDescription' in k for k in settings), f'{name}: obsolete server permission')
        if name != 'Jyotish':
            require(any(objects[d]['target'] == targets['Jyotish'] for d in target['dependencies']), f'{name}: app dependency missing')
    scheme = ET.parse(PROJECT / 'xcshareddata/xcschemes/Jyotish.xcscheme').getroot()
    for ref in scheme.iter('BuildableReference'):
        require(ref.attrib['BlueprintIdentifier'] in root['targets'], 'Scheme refers to unknown target')
    test_refs = list(scheme.findall('./TestAction/Testables/TestableReference'))
    require(len(test_refs) == 2 and all(t.attrib['skipped'] == 'NO' for t in test_refs), 'Scheme must enable both test targets')
    icon = ROOT / 'iPhoneSwiftUI/Assets.xcassets/AppIcon.appiconset'
    for image in json.loads((icon / 'Contents.json').read_text())['images']:
        require((icon / image['filename']).is_file(), 'App icon image missing')
    print(f'PASS static Xcode structure: {len(objects)} objects, 3 targets, local package, shared scheme, app assets')
    print('iOS compilation and simulator execution require Xcode on macOS; these checks do not establish either.')


if __name__ == '__main__':
    try:
        validate()
    except (ValueError, KeyError, IndexError, OSError, ET.ParseError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        sys.exit(1)
