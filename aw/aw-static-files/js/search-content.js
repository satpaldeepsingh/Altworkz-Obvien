function search() {

    var search_str = $('#search-text').val();

    if (search_str == '') {
        $('.search-validation-msg').show();
        $('#search-text').css({'border': '1px solid #d05353'});
        return false;
    }

    $('.aw_wrapper').preloader({
          text: 'Please Wait...',
          percent: '',
          duration: '',
          zIndex: '',
          setRelative: false
    });

    search_obj['search_str'] = search_str;

    if ('filters' in search_obj && search_obj['filters'].length == 0) {
        delete search_obj['filters'];   
    }

    var html;
    $.ajax({
        // url: '/api/search',
        url: '/search/elastic-search', 
        // contentType: "application/json",
        dataType : 'json',
        data: search_obj,
        // data: JSON.stringify(search_obj),
        success: function(data){

            $('.aw_section_recommendation').hide();
            $('.aw_section_recent_browse').hide();
            $('.aw_section_saved_searches').hide();
            $('.swiper-wrapper').html('');
            $('#searchResults').html('');
            $('.not-found-results').html('');
            if (swiper_instance !== null ) {
                    swiper_instance.destroy();
                    $('#resultsCarousel').hide();
            }
            if (data.results.length > 0 ){
                $('#resultsCarousel').show();
                bulleteImg = [];
                unqiue_photo_list = [];
                let result_count = 0;
                $.each(data.results, function() {
                     console.log(this);
                    if(this != false){
                        if (this['photo'] === undefined || this['photo'] == '' ||  this['photo'] === null){
                            this['photo'] = 'https://via.placeholder.com/110x110';
                        }
                        if (this['photo'] != '' && this['photo'] !== null && unqiue_photo_list.indexOf(this['photo']) === -1) {
                            bulleteImg.push(this['photo'] );
                            $('#searchResults').append(result_card(this));
                            swiper_slider(this);
                            if (this['photo'] != 'https://via.placeholder.com/110x110') {
                                unqiue_photo_list.push(this['photo']);
                            }
                            result_count++;
                        }
                    }
                });
                swiper_instance = swiper_profiles_img(); // get swiper instance for later on use
                $('.aw_section_results').show();
                $('.aw_wrapper').preloader('remove');
                $('.aw_section_title').text('Search Results ('+result_count+')');
            }
            else {
                $('.aw_section_results').hide();
                $('.aw_wrapper').preloader('remove');
                var html = '<div class="not-found-results"><div class="not-found-placeholder">No result found</div></div>';
                $('main#aw_main > .container').append(html);
            }
        },
        error: function(resp){
            console.log(resp);
        }
    });

}

function result_card(result_obj) {

    var person_name = result_obj.first_name;

    // console.log(result_obj.middle_name);

    if (result_obj.middle_name != null && result_obj.middle_name != 'NULL' && result_obj.middle_name != 'null') {
        person_name += ' ' + result_obj.middle_name;
    }

    //console.log(result_obj.last_name);

    if (result_obj.last_name != null && result_obj.last_name != 'NULL' && result_obj.last_name != 'null') {
        person_name += ' ' + result_obj.last_name;
    }

    let result_photo = empty_if_invalid_val(result_obj.photo);
    let result_full_name = empty_if_invalid_val(result_obj.full_name);
    let result_organization_title = empty_if_invalid_val(result_obj.organization_title_1);
    let current_organization = empty_if_invalid_val(result_obj.organization_1);
    let sec_source_link = empty_if_invalid_val(result_obj.sec_source_link);
    let sec_link_html = '';
    //console.log(sec_source_link);

    //'<li class="sec"><a href="#"></a></li>'+
    let source_icons = '';

    if (sec_source_link != '') {
        source_icons += `<span class="aw_card_source_icon"><a href="${sec_source_link}" target="_blank"><img src="/static/img/logos/sec.png" alt="U.S. Securities and Exchange Commission" /></a></span>`;
    }

    let ico_count = 1;
    while (result_obj['social_profile_link_'+ico_count]) {
        console.log(result_obj['platform_'+ico_count]);
        let platform_source_link = result_obj['social_profile_link_'+ico_count];
        let platform_icon = result_obj['platform_'+ico_count];
        source_icons += `<span class="aw_card_source_icon"><a href="${platform_source_link}" target="_blank"><img src="/static/img/logos/${platform_icon}.png" alt="U.S. Securities and Exchange Commission" /></a></span>`;
        ico_count++;
    }

//		var html = `<div class="col-md-4">
//			<article class="aw_card">
//				<div class="aw_card_thumb">
//					<figure><a href="#"><img src="${result_photo}" alt=""></a></figure>
//				</div>
//				<div class="aw_card_header">
//					<h3 class="aw_card_title"><a href="#">${result_full_name}</a></h3>
//					<div class="aw_card_subtitle">${result_organization_title}</div>
//					<div class="aw_card_meta">${current_organization}</div>
//				</div>
//				<div class="aw_card_footer">
//					<div class="aw_card_likes">
//						<a class="aw_thumbs_up" href="#">
//							<i class="far fa-thumbs-up"></i>
//						</a>
//						<a class="aw_thumbs_down" href="#">
//							<i class="far fa-thumbs-down"></i>
//						</a>
//						<a class="aw_thumbs_maybe" href="#">
//							<i class="far fa-thumbs-up"></i>
//						</a>
//					</div>
//					<div class="aw_card_socials">
//						<a class="facebook" href="#"><i class="fab fa-facebook-f"></i></a>
//						<a class="twitter" href="#"><i class="fab fa-twitter"></i></a>
//						<a class="google" href="#"><i class="fab fa-google"></i></a>
//					</div>
//				</div>
//			</article>
//		</div>`;

    /*

    '<ul class="aw_source_list">'+
        '<li class="bloomberg"><a href="#"><img src="/static/img/logos/bloomberg.png" alt="Bloomberg" /></a></li>'+
        '<li class="sec"><a href="#"><img src="/static/img/logos/sec.png" alt="U.S. Securities and Exchange Commission" /></a></li>'+
        '<li class="facebook"><a href="#"><i class="fab fa-facebook-f"></i></a></li>'+
        '<li class="twitter"><a href="#"><i class="fab fa-twitter"></i></a></li>'+
        '<li class="gmail"><a href="#"><i class="far fa-envelope"></i></a></li>'+
        '<li class="linkedin"><a href="#"><i class="fab fa-linkedin-in"></i></a></li>'+
    '</ul>'+

    */

    var html = `<div class="col-md-4">
        <article class="aw_card">
            <div class="aw_card_thumb">
                <figure><a href="javascript:void(0)"><img src="${result_photo}" alt=""></a></figure>
            </div>
            <div class="aw_card_header">
                <h3 class="aw_card_title"><a href="javascript:void(0)">${result_full_name}</a></h3>
                <div class="aw_card_subtitle">${result_organization_title}</div>
                <div class="aw_card_meta">${current_organization}</div>
            </div>
            <div class="aw_card_footer">
                <div class="aw_card_likes">
                <a class="aw_thumbs_up" href="javascript:void">
                    <i class="far fa-thumbs-up"></i>
                </a>
                <a class="aw_thumbs_down" href="javascript:void">
                    <i class="far fa-thumbs-down"></i>
                </a>
                <a class="aw_thumbs_maybe" href="javascript:void">
                    <i class="far fa-thumbs-up"></i>
                </a>
                </div>
                <div class="aw_card_socials">
                    ${source_icons}
                </div>
            </div>
        </article>
    </div>`;

    return html;
}

function experience_not_shown (exp_obj) {
    for (let exp_index = 0; exp_index < listed_experience.length; exp_index++) {
        if (exp_obj['org'] == listed_experience[exp_index]['org'] && exp_obj['org_title'] == listed_experience[exp_index]['org_title'] && exp_obj['org_start'] == listed_experience[exp_index]['org_start'] && exp_obj['org_end'] == listed_experience[exp_index]['org_end']) {
            return false;
        }
    }
    return true;
}

function * gen_exp_content (data) {
    let counter = 1;
    let org_counter;
    let profile_html = '';

    let listed_experience = [];

    if (data.hasOwnProperty("description") && data['description'])  {
        let description = empty_if_invalid_val(data['description']);
        `<div class='aw_card_subtitle'>Profile</div>`;
        profile_html += `<div class='aw_card_meta'>${description}</div>`
    }

    while ('organization_' + counter in data && counter <= 10) {
        let exp_info_ = '';
        let org_title = empty_if_invalid_val(data['organization_title_' + counter]);
        let org_start = empty_if_invalid_val(data['organization_start_' + counter]);
        let org_end = empty_if_invalid_val(data['organization_end_' + counter]);
        let org_counter = empty_if_invalid_val(data['organization_' + counter]);

        let job_info = {'org': org_counter, 'org_title': org_title, 'org_start': org_start, 'org_end': org_end};

        if (experience_not_shown (job_info)) {

            listed_experience.push(job_info);

            exp_info_ += `<div class='aw_card_subtitle'>${org_title}</div>`;
            if (org_start != '' || org_end != '') {
                exp_info_ += `<div class='aw_card_meta'>(${org_start} - ${org_end})</div>`;
            }
            exp_info_ += `<div class='aw_card_meta'>${org_counter}</div>`;

        }

        counter++;
        yield profile_html + exp_info_;
    }
}

function get_search_reason (data) {

    let occr_fields_list = data['occurance_fields'];
    let reasons_html = '';
    let reason_field_or_value = '';
    let text_found = '';

    // let fields_lists = ['first_name', 'last_name', 'industry', 'organization', 'organization_title_', 'description'];

    for (let ofi = 0; ofi < occr_fields_list.length; ofi++) {

        let occr_field_name = Object.keys(occr_fields_list[ofi])[0];

        if (occr_field_name == 'first_name' || occr_field_name == 'last_name') {
            reason_field_or_value = 'Name';
            text_found = data['highlights'][occr_field_name];
            let name = '';
            if (data['highlights'].hasOwnProperty('first_name')) {
                name += data['highlights']['first_name'];
            }
            if (data['highlights'].hasOwnProperty('last_name')) {
                 name += data['highlights']['last_name'];
            }

            reasons_html = `<b>Name</b> ${name}`;
        }
        else if (occr_field_name == 'industry') {
             reason_field_or_value = 'Industry';
             text_found = data['highlights'][occr_field_name];

             reasons_html = `<b>Industry</b> ${data['highlights']['industry']}`;
        }
        else if (occr_field_name.indexOf('organization_title_') > -1) {
             reason_field_or_value = 'job ';
             let curr_or_prev = '';
             let job_title = '';
             if (occr_field_name.match(/_(\d+$)/)[0].slice(1) == '1') {
                curr_or_prev = 'Current';
                job_title = data['job_title'];
             }
             else {
                curr_or_prev = 'Past';
                job_title = occr_fields_list[ofi][occr_field_name];
             }

             reasons_html = `<b>${curr_or_prev} ${reason_field_or_value}</b> ${job_title}`;
        }
        else if (occr_field_name.indexOf('organization_') > -1) {
             reason_field_or_value = data['highlights']['organization_name'];
             let curr_or_prev = '';
             if (occr_field_name.match(/_(\d+$)/)[0].slice(1) == '1') {
                curr_or_prev = 'Current';
             }
             else {
                curr_or_prev = 'Past';
             }
             reason_field_or_value = reason_field_or_value;
             text_found = occr_fields_list[ofi][occr_field_name];
             reasons_html = `<b>${curr_or_prev} org.</b> ${reason_field_or_value}`;
        }

        break;

    }

    if (occr_fields_list.length === 0) {

          text_found = data['highlights']['description'][0];
          reasons_html = `<b>Profile</b> ${text_found}`;

    }

    return reasons_html;

}


function swiper_slider(data){
    var company = '';
    var job_title = '';

    if(data.hasOwnProperty('organization_1')){
        company = empty_if_invalid_val(data['organization_1']);
        job_title = empty_if_invalid_val(data['organization_title_1']);
    }

    let reasons_content = get_search_reason(data);

    var expereince_string = '';
    var card_body = '';
    var reason = '';
    for (const exp_info of gen_exp_content(data)) {
        card_body += exp_info;
    }

    let full_name = empty_if_invalid_val(data['full_name']);
    let sec_source_link = empty_if_invalid_val(data['sec_source_link']);
    let industry = empty_if_invalid_val(data['industry']);

    let icon_list_items = '';
    if (sec_source_link != '') {
        icon_list_items += `<li class="sec"><a href="${sec_source_link}" target="_blank"><img src="/static/img/logos/sec.png" alt="U.S. Securities and Exchange Commission" /></a></li>`;
    }

    let ico_count = 1;
    while (data['social_profile_link_'+ico_count]) {
        // console.log(data['platform_'+ico_count]);
        let platform_source_link = data['social_profile_link_'+ico_count];
        let platform_icon = data['platform_'+ico_count];
        //icon_list_items += `<span class="aw_card_source_icon"><a href="${platform_source_link}" target="_blank"><img src="/static/img/logos/${platform_icon}.png" alt="U.S. Securities and Exchange Commission" /></a></span>`;
        icon_list_items += `<li class="sec"><a href="${platform_source_link}" target="_blank"><img src="/static/img/logos/${platform_icon}.png" alt="Bloomberg" /></a></li>`;
        
        ico_count++;
    }  

    var article_counter = 0;
    var html = '<div class="swiper-slide">'+
                    '<article class="aw_card">'+
                        '<div class="aw_card_header">'+
                            '<div class="aw_card_thumb">'+
                                '<figure>'+
                                    '<a href="#"><img src="' + data['photo'] + '" alt="' + full_name + '" /></a>'+
                                '</figure>'+
                            '</div>'+
                            '<div class="aw_card_info">'+
                                '<h3 class="aw_card_title">'+
                                    '<a href="#">' + full_name + '</a>'+
                                '</h3>'+
                                '<div class="aw_card_subtitle">'+ job_title +'</div>'+
                                '<div class="aw_card_meta">'+ company +'</div>'+
                                '<div class="aw_card_meta">'+ industry +'</div>'+
                                '<ul class="aw_source_list">'+
                                    //'<li class="bloomberg"><a href="#"><img src="/static/img/logos/bloomberg.png" alt="Bloomberg" /></a></li>'+
                                    icon_list_items+
                                    //'<li class="facebook"><a href="#"><i class="fab fa-facebook-f"></i></a></li>'+
                                    //'<li class="twitter"><a href="#"><i class="fab fa-twitter"></i></a></li>'+
                                    //'<li class="gmail"><a href="#"><i class="far fa-envelope"></i></a></li>'+
                                    //'<li class="linkedin"><a href="#"><i class="fab fa-linkedin-in"></i></a></li>'+
                                '</ul>'+
                                //'<a href="javascript:void" class="search">'+
                                    // '<span class="d-inline-block" tabindex="0" data-toggle="tooltip" data-placement="bottom" data-html="true" title="<em>Tooltip</em> <u>with</u> <b>HTML</b>">'+
                                    //     '<button class="btn btn-primary btn-sm result-reasons" style="pointer-events: none;" type="button" disabled>Reaon(s)</button>'+
                                    // '</span>'+
                                //'<button type="button" class="btn btn-primary btn-sm result-reasons" data-toggle="tooltip" data-placement="bottom" data-html="true" title="<em>Tooltip</em> <u>with</u> <b>HTML</b>">Reaon(s)</button>'+
                                //'</a>'+
                            '</div>'+
                        '</div>'+
                        '<div class="aw_card_reason"><p>'+reasons_content+'</p></div>'+
                        '<div class="aw_card_body" style="border-top:1px solid #cccccc">'+
                            '<h6>Profile</h6>'+
                            card_body +
                        '</div>'+
                    '</article>'+
                '</div>';
        $('.swiper-wrapper').append(html);
}

function swiper_profiles_img () {
    var mySwiper = new Swiper('.swiper-container', {
        autoHeight: true,
        observer: true,
        observeParents: true,
        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev'
        },
        pagination: {
            el: '.swiper-pagination',
            clickable: true,
            renderBullet: function (index, className) {
                return `<div class="${className}"><img src="${bulleteImg[index]}" /></div>`;
            },
            dynamicBullets: true,
            dynamicMainBullets: 1
        },
    });

    return mySwiper;

     //mySwiper.slideTo(2);
}


function empty_if_invalid_val (value) {
    if (typeof value === 'undefined' || value == null || value == 'null' || value == 'NULL') {
        return '';
    }
    return value;
}

function capitalize_1st_letter (str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}