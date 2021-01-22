
$(document).ready(function () {
    $('#pathSearch').search({
        apiSettings: {
            response: function (e) {
                let path = document.getElementById('path').value;
                let response = checkProjectDirectory(path);

                let results = [];
                for (const subdir of response.subdirs) {
                    results.push({title: subdir})
                }

                return {results: results}
            }
        },
        showNoResults: false,
        cache: false
    });

    $('#newProjectForm').form({
        fields: {
            name: {
                rules: [
                    {
                        type   : 'empty',
                        prompt : 'Please enter a project name'
                    },
                    {
                        type: 'uniqueProjectName[]',
                        prompt: 'The chosen project name already exists'
                    }
                ]
            },
            path: {
                rules: [
                    {
                        type   : 'empty',
                        prompt : 'Please enter a path'
                    },
                    {
                        type: 'existingPath',
                        prompt: 'The chosen directory already exists'
                    }
                ]
            }
        }
    });

    $('#pathSearchImport').search({
        apiSettings: {
            response: function (e) {
                let path = document.getElementById('path').value;
                let response = checkProjectDirectory(path);

                results = [];
                for (const subdir of response.subdirs) {
                    results.push({title: subdir})
                }

                updateClassList(response.classes);
                // TODO: Disable editing

                return {results: results}
            }
        },
        onSelect: function (selectedResult, resultList) {
            let classes = checkProjectDirectory(selectedResult.title).classes;
            updateClassList(classes);
        },
        showNoResults: false,
        cache: false
    });

    let relocateProjectName = '';
    let nameInput = $('#name');
    if (nameInput) {
        relocateProjectName = nameInput.val();
    }
    let relocateProjectPath = '';
    let pathInput = $('#path');
    if (pathInput) {
        relocateProjectPath = pathInput.val();
    }

    $('#importProjectForm').form({
        fields: {
            name: {
                rules: [
                    {
                        type   : 'empty',
                        prompt : 'Please enter a project name'
                    },
                    {
                        type: 'uniqueProjectName[' + relocateProjectName + ']',
                        prompt: 'The chosen project name already exists'
                    }
                ]
            },
            path: {
                rules: [
                    {
                        type   : 'empty',
                        prompt : 'Please enter a path'
                    },
                    {
                        type: 'notExistingPath',
                        prompt: 'The chosen directory doesn\'t exists'
                    },
                    {
                        type: 'uniquePath[' + relocateProjectPath + ']',
                        prompt: 'Another project is already initialized in this location'
                    }
                ]
            }
        }
    });

    $('.hasclickpopup').popup({
        inline: true,
        on: 'click',
        position: 'bottom right',
    });

    $('.hashoverpopup').popup();
});


$.fn.form.settings.rules.uniqueProjectName = function (projectName, relocatedName) {
    if (relocatedName && projectName === relocatedName) {
        return true;
    }

    let projects = getProjects();
    let projectNames = Object.keys(projects);
    return !projectNames.includes(projectName);
}


$.fn.form.settings.rules.existingPath = function (projectPath) {
    let response = checkProjectDirectory(projectPath);
    return !response.path_exists;
}


$.fn.form.settings.rules.notExistingPath = function (projectPath) {
    let response = checkProjectDirectory(projectPath);
    return response.path_exists;
}


$.fn.form.settings.rules.uniquePath = function (projectPath, relocatedPath) {
    if (relocatedPath && projectPath === relocatedPath) {
        return true;
    }

    let projects = getProjects();
    for (project of Object.values(projects)) {
        if (project.path === projectPath) {
            return false;
        }
    }
    return true;
}


function syncRequest(url, data) {
    let xhttp = new XMLHttpRequest();

    xhttp.open('POST', url, false);
    xhttp.setRequestHeader('Content-type', 'application/json; charset=utf-8');

    if (data) {
        xhttp.send(JSON.stringify(data));
    } else {
        xhttp.send();
    }

    return JSON.parse(xhttp.responseText);
}


function getProjects() {
    return syncRequest('/projects-list', null);
}


function checkProjectDirectory(path) {
    return syncRequest('/check-existing-project', {path: path});
}


function updateClassList(classes) {
    let classList = document.getElementById('classList');

    while (classList.firstChild) {
        classList.removeChild(classList.lastChild);
    }

    for (const className of classes){
        addClassInput(className);
    }
}


function addClassInput(className) {
    let classList = document.getElementById('classList');
    let numClasses = classList.children.length;

    // Create new row
    let row = document.createElement('div');
    row.className = 'three fields';

    classField = document.createElement('div');
    classField.className = 'field';
    classInputGroup = createInputWithLabel('eye', 'Class', 'class' + numClasses, className, true)
    classField.appendChild(classInputGroup);
    row.appendChild(classField);

    tag1Field = document.createElement('div');
    tag1Field.className = 'field';
    tag1InputGroup = createInputWithLabel('tag', 'Tag 1', 'class' + numClasses + '_tag1', '', false)
    tag1Field.appendChild(tag1InputGroup);
    row.appendChild(tag1Field);

    tag2Field = document.createElement('div');
    tag2Field.className = 'field';
    tag2InputGroup = createInputWithLabel('tag', 'Tag 2', 'class' + numClasses + '_tag2', '', false)
    tag2Field.appendChild(tag2InputGroup);
    row.appendChild(tag2Field);

    classList.appendChild(row);

    // Remove onfocus handler on previous node
    if (numClasses > 0) {
        let previousLabeledInput = classList.children[numClasses - 1].children[0].children[0];
        let previousInput = previousLabeledInput.children[previousLabeledInput.children.length - 1];
        previousInput.removeAttribute('onfocus');
    }
}

function createInputWithLabel(icon, labelText, name, prefill, addOnFocus) {
    let inputGroup = document.createElement('div');
    inputGroup.className = 'ui labeled input';

    let label = document.createElement('div');
    label.className = 'ui label';

    let iconElement = document.createElement('i');
    iconElement.className = icon + ' icon';

    label.appendChild(iconElement);
    label.appendChild(document.createTextNode(' ' + labelText + ' '));
    inputGroup.appendChild(label);

    let input = document.createElement('input');
    input.type = 'text';
    input.name = name;
    input.value = prefill;
    input.placeholder = name;

    if (addOnFocus) {
        input.setAttribute('onfocus', 'addClassInput("");');
    }

    inputGroup.appendChild(input);
    return inputGroup
}

function loading(element) {
    element.classList.add('loading');
    element.classList.add('disabled');
}


let tagColors = [
    'grey',
    'blue',
    'green'
]

function assignTag(frameIdx, selectedTagIdx) {
    let tagInput = document.getElementById(frameIdx + '_tag');
    tagInput.value = selectedTagIdx;

    for (const tagIdx of [0, 1, 2]) {
        let button = document.getElementById(frameIdx + '_tag' + tagIdx);

        if (tagIdx == selectedTagIdx) {
            button.classList.add(tagColors[tagIdx]);
        } else {
            button.classList.remove(tagColors[tagIdx]);
        }
    }
}
