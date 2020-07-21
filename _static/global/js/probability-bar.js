let probabilityBarComponent = {
    props: {
        label: String,
        percent: Number,
    },
    data: function () {
        return {
            defenseTokens: []
        }
    },
    template:
        `
        <div>
            <div class="title-small">{{ label }}: <strong>{{percent}}%</strong></div>
            <div class='bar'>
                <div class="innocent" :style="{'width':(percent+'%')}">
                </div>
            </div>
        </div>
        `
}