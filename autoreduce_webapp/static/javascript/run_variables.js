(function(){
    var formUrl = $('#run_variables').attr('action');

    var isNumber = function isNumber(n){
        return !isNaN(parseFloat(n)) && isFinite(n);
    };

    String.prototype.endsWith = function(suffix) {
        return this.indexOf(suffix, this.length - suffix.length) !== -1;
    };

    var previewScript  = function previewScript(){
        var url = $('#preview_url').val();
        var $form = $('#run_variables');
        if($form.length===0) $form = $('#instrument_variables');
        $form.attr('action', url);
        $form.submit();
    };

    var validateForm = function validateForm(){
        var isValid = true;
        var $form = $('#run_variables');
        if($form.length===0) $form = $('#instrument_variables');

        var resetValidationStates = function resetValidationStates(){
            $('.has-error').removeClass('has-error');
        };

        var validateNotEmpty = function validateNotEmpty(){
            if($(this).val().trim() === ''){
                $(this).parent().addClass('has-error');
                isValid = false;
            }
        };
        var validateText = function validateText(){
            validateNotEmpty.call(this);
        };
        var validateNumber = function validateNumber(){
            validateNotEmpty.call(this);
            if(!isNumber($(this).val())){
                $(this).parent().addClass('has-error');
                isValid = false;
            }
        };
        var validateBoolean = function validateBoolean(){
            validateNotEmpty.call(this);
            if($(this).val().toLowerCase() !== 'true' && $(this).val().toLowerCase() !== 'false'){
                $(this).parent().addClass('has-error');
                isValid = false;
            }
        };
        var validateListNumber = function validateListNumber(){
            var items, i;
            validateNotEmpty.call(this);
            if($(this).val().trim().endsWith(',')){
                $(this).parent().addClass('has-error');
                isValid = false;
            }else{
                items = $(this).val().split(',');
                for(i=0;i<items.length;i++){
                    if(!isNumber(items[i])){
                        $(this).parent().addClass('has-error');
                        isValid = false;
                        break;
                    }
                }
            }
        };
        var validateListText = function validateListText(){
            var items, i;
            validateNotEmpty.call(this);
            if($(this).val().trim().endsWith(',')){
                $(this).parent().addClass('has-error');
                isValid = false;
            }else{
                items = $(this).val().split(',');
                for(i=0;i<items.length;i++){
                    if(items[i].trim() === ''){
                        $(this).parent().addClass('has-error');
                        isValid = false;
                        break;
                    }
                }
            }
        };

        // Populate all boolean values with their checked state
        $('[data-type="boolean"]').each(function(){
            if($(this).attr('checked')){
                $(this).val('True');
            }else{
                $(this).val('False');
            }
        });

        resetValidationStates();
        $('[data-type="text"]').each(validateText);
        $('[data-type="number"]').each(validateNumber);
        $('[data-type="boolean"]').each(validateBoolean);
        $('[data-type="list_number"]').each(validateListNumber);
        $('[data-type="list_text"]').each(validateListText);

        return isValid;
    };

    var triggerAfterRunOptions = function triggerAfterRunOptions(){
        if($(this).val().trim() !== ''){
            $('#next_run').text(parseInt($(this).val())+1);
            $('#run_finish_warning').show();
        }else{
            $('#run_finish_warning').hide();
        }
    };

    var showDefaultSriptVariables = function showDefaultSriptVariables(){
        $('#default-variables-modal').modal();
    };

    var checkForConflicts = function checkForConflicts(successCallback, cancelCallback){
        var start = parseInt($('#run_start').val());
        var end = parseInt($('#run_end').val());
        var upcoming = $('#upcoming_runs').val().split(',');
        var conflicts = [];
        for(var i=0;i<upcoming.length;i++){
            if(parseInt(upcoming[i]) >= start && (end == NaN || upcoming[i] <= end)){
                conflicts.push(upcoming[i]);
            }
        }
        if(conflicts.length === 0){
            successCallback();
        }else{
            $('#conflicts-modal js-conflicts-cancel').unbind('click').on('click', cancelCallback);
            $('#conflicts-modal js-conflicts-confirm').unbind('click').on('click', successCallback);
            $('#conflicts-modal').modal();
        }
    };

    var submitForm = function submitForm(event){
        var submitAction = function submitAction(){
            var $form = $('#run_variables');
            if($form.length===0) $form = $('#instrument_variables');
            $form.attr('action', formUrl);
            $form.submit();
        };
        var cancelAction = function cancelAction(){
            return false;
        };

        event.preventDefault();
        if(validateForm()){
            checkForConflicts(submitAction, cancelAction);
        }else{
            cancelAction();
        }
    };
    
    var init = function init(){
        $('#previewScript').on('click', previewScript);
        $('#variableSubmit').on('click', submitForm);
        $('#run_end').on('change', triggerAfterRunOptions);
        $('.js-show-default-variables').on('click', showDefaultSriptVariables);
    };

    init();
}())